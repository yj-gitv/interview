"""
面试助手 - 桌面启动器
双击即可启动服务并打开浏览器。
"""

import os
import sys
import signal
import socket
import threading
import time
import webbrowser

# When running as a PyInstaller bundle, ensure the working directory is next to the exe
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(sys.executable))

# Add backend to sys.path so `app` package is importable
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if os.path.isdir(backend_dir):
    sys.path.insert(0, backend_dir)
else:
    sys.path.insert(0, os.getcwd())

HOST = "127.0.0.1"
PORT = int(os.environ.get("APP_PORT", "3000"))
URL = f"http://{HOST}:{PORT}"


def _port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, port)) != 0


def _wait_and_open_browser():
    """Wait until the server is accepting connections, then open browser."""
    for _ in range(60):
        time.sleep(0.5)
        if not _port_available(PORT):
            webbrowser.open(URL)
            return
    print(f"[启动器] 警告: 服务未在 {PORT} 端口响应", flush=True)


def _ensure_dirs():
    for d in ("data", "uploads", "exports"):
        os.makedirs(d, exist_ok=True)


def main():
    _ensure_dirs()

    if not _port_available(PORT):
        print(f"[启动器] 端口 {PORT} 已被占用，面试助手可能已在运行。")
        print(f"[启动器] 正在打开 {URL}")
        webbrowser.open(URL)
        return

    print("=" * 50)
    print("         面试助手 v1.0.0")
    print("=" * 50)
    print()
    print(f"  服务地址: {URL}")
    print(f"  数据目录: {os.path.abspath('data')}")
    print()
    print("  启动中，请稍候...")
    print()
    print("  提示: 关闭此窗口即可停止服务")
    print("=" * 50)
    print()

    # Open browser in background once server is ready
    threading.Thread(target=_wait_and_open_browser, daemon=True).start()

    import uvicorn
    from app.main import app

    # Graceful shutdown on Ctrl+C / window close
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
    try:
        signal.signal(signal.SIGBREAK, lambda *_: sys.exit(0))
    except (AttributeError, OSError):
        pass

    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
