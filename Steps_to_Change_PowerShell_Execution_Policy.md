# Steps to Change PowerShell Execution Policy

PowerShell's execution policy determines the conditions under which PowerShell loads configuration files and runs scripts. Follow these steps to change the execution policy:

1. **Open PowerShell as Administrator**
   - Search for "PowerShell" in the Start menu.
   - Right-click on "Windows PowerShell" and select "Run as Administrator."

2. **Check the Current Execution Policy**
   - Run the following command to view the current execution policy:
     ```powershell
     Get-ExecutionPolicy
     ```

3. **Change the Execution Policy**
   - Use the `Set-ExecutionPolicy` cmdlet to change the execution policy. For example, to set the policy to `RemoteSigned`, run:
     ```powershell
     Set-ExecutionPolicy RemoteSigned
     ```
   - You can replace `RemoteSigned` with other policies like `Restricted`, `AllSigned`, `Unrestricted`, etc., depending on your requirements.

4. **Confirm the Change**
   - You may be prompted to confirm the change. Type `Y` and press Enter.

5. **Verify the New Execution Policy**
   - Run the following command to ensure the policy has been updated:
     ```powershell
     Get-ExecutionPolicy
     ```

6. **Optional: Set Execution Policy for Current Session Only**
   - If you want to set the execution policy for the current session only, use the `-Scope` parameter:
     ```powershell
     Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
     ```

7. **Revert Back from RemoteSigned**
   - To revert the execution policy back to its default or another policy, use the `Set-ExecutionPolicy` cmdlet again. For example, to revert to `Restricted`:
     ```powershell
     Set-ExecutionPolicy Restricted
     ```
   - Confirm the change and verify it using the `Get-ExecutionPolicy` command.

## PowerShell Execution Policy Options

Here are the different execution policy options available in PowerShell:

- **Restricted**: Does not load configuration files or run scripts. This is the default setting.
- **AllSigned**: Only runs scripts signed by a trusted publisher. Prompts for confirmation before running scripts from new publishers.
- **RemoteSigned**: Requires that all scripts and configuration files downloaded from the internet be signed by a trusted publisher.
- **Unrestricted**: Loads all configuration files and runs all scripts. Warns the user before running scripts downloaded from the internet.
- **Bypass**: Nothing is blocked, and there are no warnings or prompts.
- **Undefined**: Removes the currently assigned execution policy from the current scope. If all scopes are set to Undefined, the default policy (Restricted) is applied.

**Note:**
- Changing the execution policy might expose your system to security risks. Always ensure you understand the implications of the policy you choose.
- To learn more about execution policies, run:
  ```powershell
  Get-Help about_Execution_Policies
  ```