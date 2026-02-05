#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Cross-platform desktop notifications for Stop and Notification events.

Opt-in via OMC_NOTIFICATIONS=1 environment variable.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hook_utils import hook_main, log_debug, output_empty, parse_hook_input, read_stdin_safe


def _sanitize_applescript(value: str) -> str:
    """Sanitize string for safe AppleScript interpolation.

    Security fix: prevents command injection via backslash and quote escaping.
    """
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _sanitize_powershell(value: str) -> str:
    """Sanitize string for safe PowerShell single-quoted interpolation.

    Security fix: doubles single quotes, which is PowerShell's escape for them.
    """
    return value.replace("'", "''")


def get_notifier_command(title: str, message: str) -> list[str] | None:
    """Get platform-appropriate notification command."""

    if sys.platform == "darwin":
        # macOS - osascript always available
        # Security: sanitize to prevent AppleScript injection
        safe_title = _sanitize_applescript(title)
        safe_message = _sanitize_applescript(message)
        script = f'display notification "{safe_message}" with title "{safe_title}"'
        return ["osascript", "-e", script]

    elif sys.platform == "win32":
        # Windows - PowerShell toast
        # Security: sanitize and use single-quoted strings to prevent injection
        safe_title = _sanitize_powershell(title)
        safe_message = _sanitize_powershell(message)
        ps_script = f'''
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        $template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
        $xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template)
        $xml.GetElementsByTagName("text")[0].AppendChild($xml.CreateTextNode('{safe_title}')) | Out-Null
        $xml.GetElementsByTagName("text")[1].AppendChild($xml.CreateTextNode('{safe_message}')) | Out-Null
        $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Claude Code").Show($toast)
        '''
        return ["powershell", "-Command", ps_script]

    else:
        # Linux/BSD - check for common notifiers
        # First check if WSL
        try:
            version_info = Path("/proc/version").read_text().lower()
            if "microsoft" in version_info or "wsl" in version_info:
                # WSL - use Windows PowerShell
                # Security: sanitize and use single-quoted strings to prevent injection
                safe_title = _sanitize_powershell(title)
                safe_message = _sanitize_powershell(message)
                ps_script = f'''
                Add-Type -AssemblyName System.Windows.Forms
                $balloon = New-Object System.Windows.Forms.NotifyIcon
                $balloon.Icon = [System.Drawing.SystemIcons]::Information
                $balloon.BalloonTipTitle = '{safe_title}'
                $balloon.BalloonTipText = '{safe_message}'
                $balloon.Visible = $true
                $balloon.ShowBalloonTip(5000)
                Start-Sleep -Milliseconds 5100
                $balloon.Dispose()
                '''
                return ["powershell.exe", "-Command", ps_script]
        except Exception:
            pass

        # Try Linux notifiers in order of preference
        if shutil.which("notify-send"):
            return ["notify-send", title, message]
        elif shutil.which("zenity"):
            return ["zenity", "--notification", f"--text={title}: {message}"]
        elif shutil.which("kdialog"):
            return ["kdialog", "--passivepopup", message, "5", "--title", title]

        # No notifier found
        return None


def send_notification(title: str, message: str) -> bool:
    """Send notification, return True if successful."""
    cmd = get_notifier_command(title, message)

    if cmd is None:
        log_debug("No notification tool found on this system")
        return False

    try:
        log_debug(f"Sending notification via: {cmd[0]}")
        subprocess.run(cmd, capture_output=True, timeout=10)
        return True
    except subprocess.TimeoutExpired:
        log_debug("Notification command timed out")
        return False
    except Exception as e:
        log_debug(f"Notification failed: {e}")
        return False


@hook_main("Notification")
def main() -> None:
    # Check if enabled (opt-in)
    if os.environ.get("OMC_NOTIFICATIONS", "0") != "1":
        log_debug("Notifications disabled (set OMC_NOTIFICATIONS=1 to enable)")
        output_empty()
        return

    data = parse_hook_input(read_stdin_safe())
    if not data:
        output_empty()
        return

    hook_event = data.get("hook_event_name", "")
    log_debug(f"Notification hook triggered for event: {hook_event}")

    if hook_event == "Stop":
        send_notification("Claude Code", "Task completed")
    elif hook_event == "Notification":
        # Get notification type from matcher context
        notification_type = data.get("notification_type", "attention needed")
        send_notification("Claude Code", f"Attention: {notification_type}")
    else:
        log_debug(f"Unhandled event type: {hook_event}")

    # Never block workflow
    output_empty()


if __name__ == "__main__":
    main()  # pyright: ignore[reportCallIssue]
