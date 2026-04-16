"""WhatsApp MCP launcher.

No flags  → start Beeper + MCP HTTP server + system-tray icon.
--install → create a Desktop shortcut that calls this script (one-time setup).
"""

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
BEEPER_EXE = Path.home() / "AppData/Local/Programs/BeeperTexts/Beeper.exe"
ICON_PATH = HERE / "beeper.ico"
PYTHONW = HERE / ".venv/Scripts/pythonw.exe"
DESKTOP = Path.home() / "Desktop"


def install():
    import winreg
    lnk = DESKTOP / "Beeper.lnk"

    ps = f"""
$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}')
$s.TargetPath = '{PYTHONW}'
$s.Arguments = 'run.py'
$s.WorkingDirectory = '{HERE}'
$s.IconLocation = '{BEEPER_EXE},0'
$s.WindowStyle = 7
$s.Save()
"""
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], check=True)
    print(f"Shortcut created: {lnk}")


def main():
    import pystray
    from PIL import Image

    LOG_PATH = HERE / "logs" / "tray.log"
    LOG_PATH.parent.mkdir(exist_ok=True)
    log = LOG_PATH.open("a", buffering=1)

    subprocess.Popen([str(BEEPER_EXE)], creationflags=subprocess.DETACHED_PROCESS)

    uv = shutil.which("uv")
    mcp_proc = subprocess.Popen(
        [uv, "run", "fastmcp", "run", "server.py", "--transport", "http", "--port", "23380"],
        cwd=str(HERE),
        stdout=log,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    def quit_app(icon, _item):
        mcp_proc.terminate()
        icon.stop()

    icon = pystray.Icon(
        "whatsapp-mcp",
        Image.open(ICON_PATH),
        "WhatsApp MCP (Beeper)",
        menu=pystray.Menu(pystray.MenuItem("Quit MCP", quit_app)),
    )
    icon.run()


if __name__ == "__main__":
    if "--install" in sys.argv:
        install()
    else:
        main()
