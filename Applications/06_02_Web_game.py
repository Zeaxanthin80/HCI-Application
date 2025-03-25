"""
Enhanced Face-Controlled Game Interface

This script implements a face detection-based game controller using OpenCV and PyAutoGUI.
It allows users to control games using face movements, with features like:
- Adaptive control box sizing
- Visual feedback
- Calibration phase
- Pause functionality
- Performance monitoring
"""

import cv2
import numpy as np
import pyautogui as gui
import time
import threading

# Disable PyAutoGUI's delay between actions for more responsive controls
gui.PAUSE = 0

# Paths to the pre-trained face detection model files
# The model uses a Single Shot Detector (SSD) with ResNet base network
model_path = './model/res10_300x300_ssd_iter_140000.caffemodel'
prototxt_path = './model/deploy.prototxt'

# Game state constants for better state management
GAME_STATES = {
    'CALIBRATION': 0,  # Initial state where user centers their face
    'RUNNING': 1,      # Game is active and accepting inputs
    'PAUSED': 2       # Game is paused, no inputs processed
}

def detect(net, frame):
    """
    Detect faces in a video frame using the pre-trained deep neural network.
    
    Args:
        net (cv2.dnn.Net): The loaded neural network model
        frame (numpy.ndarray): Input video frame
        
    Returns:
        list: List of dictionaries containing detected face information:
              - 'start': (x,y) coordinates of top-left corner
              - 'end': (x,y) coordinates of bottom-right corner
              - 'confidence': Detection confidence score
    """
    detected_faces = []
    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(
        cv2.resize(frame, (300, 300)),
        1.0,
        (300, 300),
        (104.0, 177.0, 123.0))
    net.setInput(blob)
    detections = net.forward()
    for i in range(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.5:
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")
            detected_faces.append({
                'start': (startX, startY),
                'end': (endX, endY),
                'confidence': confidence})
    return detected_faces

def drawFace(frame, detected_faces, action=None):
    """
    Draw visual indicators for detected faces and current actions.
    
    Args:
        frame (numpy.ndarray): Input video frame
        detected_faces (list): List of detected face dictionaries
        action (str, optional): Current action being performed (e.g., 'LEFT', 'RIGHT')
        
    Returns:
        numpy.ndarray: Frame with visual indicators drawn
    """
    for face in detected_faces:
        # Draw face rectangle in green
        cv2.rectangle(frame, face['start'], face['end'], (0, 255, 0), 3)
        
        # Show action feedback if provided
        if action:
            text_pos = (face['start'][0], face['start'][1] - 10)
            cv2.putText(frame, action, text_pos, 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    return frame

def calculate_control_box(frame_width, frame_height):
    """
    Calculate the dimensions of the control box based on frame size.
    
    The box is sized proportionally to the frame dimensions with maximum limits
    to ensure it stays manageable on large displays.
    
    Args:
        frame_width (int): Width of the video frame
        frame_height (int): Height of the video frame
        
    Returns:
        list: [left_x, right_x, bottom_y, top_y] coordinates of control box
    """
    box_width = min(300, frame_width // 3)
    box_height = min(400, frame_height // 2)
    
    left_x = frame_width // 2 - box_width // 2
    right_x = frame_width // 2 + box_width // 2
    top_y = frame_height // 2 - box_height // 2
    bottom_y = frame_height // 2 + box_height // 2
    
    return [left_x, right_x, bottom_y, top_y]

def checkRect(detected_faces, bbox):
    """
    Check if any detected face is within the control box bounds.
    
    This function is used both for calibration and determining when
    the face is in the neutral/center position.
    
    Args:
        detected_faces (list): List of detected face dictionaries
        bbox (list): Control box coordinates [left_x, right_x, bottom_y, top_y]
        
    Returns:
        bool: True if a face is within bounds, False otherwise
    """
    for face in detected_faces:
        x1, y1 = face['start']
        x2, y2 = face['end']
        if x1 > bbox[0] and x2 < bbox[1]:
            if y1 > bbox[3] and y2 < bbox[2]:
                return True
    return False

def move(detected_faces, bbox):
    """
    Convert face position to keyboard commands for game control.
    
    The function implements a simple state machine:
    1. If face is centered -> no action
    2. If face was previously centered and moves:
       - Left side of box -> press left arrow
       - Right side of box -> press right arrow
       - Above box -> press up arrow
       - Below box -> press down arrow
    
    Args:
        detected_faces (list): List of detected face dictionaries
        bbox (list): Control box coordinates
        
    Returns:
        str: Action being performed for visual feedback
    """
    global last_mov
    action = None
    
    for face in detected_faces:
        x1, y1 = face['start']
        x2, y2 = face['end']

        # Center
        if checkRect(detected_faces, bbox):
            last_mov = 'center'
            action = 'CENTER'
            return action

        elif last_mov == 'center':
            # Left
            if x1 < bbox[0]:
                gui.press('left')
                last_mov = 'left'
                action = 'LEFT'
            # Right
            elif x2 > bbox[1]:
                gui.press('right')
                last_mov = 'right'
                action = 'RIGHT'
            # Down
            if y2 > bbox[2]:
                gui.press('down')
                last_mov = 'down'
                action = 'DOWN'
            # Up
            elif y1 < bbox[3]:
                gui.press('up')
                last_mov = 'up'
                action = 'UP'

    return action

def show_calibration_guide(frame):
    """
    Display calibration instructions on the video frame.
    
    Helps users understand how to start the game by showing
    text instructions for face positioning.
    
    Args:
        frame (numpy.ndarray): Input video frame
        
    Returns:
        numpy.ndarray: Frame with calibration instructions
    """
    h, w = frame.shape[:2]
    text = "Position your face in the box and press SPACE to start"
    cv2.putText(frame, text, (w//2 - 200, h//2), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    return frame

def load_model_async(prototxt_path, model_path):
    """
    Load the neural network model asynchronously.
    Returns the loaded model.
    """
    return cv2.dnn.readNetFromCaffe(prototxt_path, model_path)

def play(prototxt_path, model_path):
    """
    Main game loop implementing the face-controlled interface.
    """
    global last_mov
    
    # Initialize camera first
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera")
        return

    # Start loading the model in a separate thread
    model_thread = threading.Thread(target=lambda: load_model_async(prototxt_path, model_path))
    model_thread.start()

    # Get frame dimensions
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    bbox = calculate_control_box(frame_width, frame_height)
    
    # Initialize window with camera feed immediately
    while model_thread.is_alive():
        ret, frame = cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            cv2.putText(frame, "Loading face detection model...", (50, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.imshow('Face Control Game', frame)
            if cv2.waitKey(1) & 0xFF == 27:  # Allow ESC to exit during loading
                cap.release()
                cv2.destroyAllWindows()
                return

    # Wait for model to finish loading
    model_thread.join()
    net = load_model_async(prototxt_path, model_path)
    
    # Get screen resolution for mouse positioning
    screen_width, screen_height = gui.size()
    
    # Initialize other variables
    game_state = GAME_STATES['CALIBRATION']
    prev_frame_time = time.time()
    last_mov = ''

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame")
            break

        frame = cv2.flip(frame, 1)
        detected_faces = detect(net, frame)
        
        # Calculate FPS
        new_frame_time = time.time()
        fps = int(1 / (new_frame_time - prev_frame_time))
        prev_frame_time = new_frame_time
        
        # Draw control box
        frame = cv2.rectangle(
            frame, (bbox[0], bbox[3]), (bbox[1], bbox[2]), 
            (0, 0, 255) if game_state == GAME_STATES['CALIBRATION'] else (255, 0, 0), 
            3)
        
        if game_state == GAME_STATES['CALIBRATION']:
            frame = show_calibration_guide(frame)
            if checkRect(detected_faces, bbox):
                frame = drawFace(frame, detected_faces, "READY!")
            else:
                frame = drawFace(frame, detected_faces)
                
        elif game_state == GAME_STATES['RUNNING']:
            action = move(detected_faces, bbox)
            frame = drawFace(frame, detected_faces, action)
        
        elif game_state == GAME_STATES['PAUSED']:
            frame = drawFace(frame, detected_faces)
            cv2.putText(frame, "PAUSED - Press SPACE to resume", 
                       (frame_width//2 - 200, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Show FPS
        cv2.putText(frame, f"FPS: {fps}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow('Face Control Game', frame)
        
        # Handle key events
        key = cv2.waitKey(1)
        if key == 27:  # ESC
            break
        elif key == 32:  # SPACE
            if game_state == GAME_STATES['CALIBRATION']:
                if checkRect(detected_faces, bbox):
                    game_state = GAME_STATES['RUNNING']
                    last_mov = 'center'
                    # Click in the center of the screen
                    gui.click(x=screen_width//2, y=screen_height//2)
            elif game_state == GAME_STATES['RUNNING']:
                game_state = GAME_STATES['PAUSED']
            elif game_state == GAME_STATES['PAUSED']:
                game_state = GAME_STATES['RUNNING']

    cap.release()
    cv2.destroyAllWindows()

# Global variables
if __name__ == "__main__":
    # last_mov tracks the previous movement to prevent input "drifting"
    last_mov = ''
    play(prototxt_path, model_path)
