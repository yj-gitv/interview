"""
面试助手 - 启动器
双击运行后自动启动后端服务并打开浏览器。
"""

import os
import sys
import time
import signal
import webbrowser
import threading
import subprocess


def get_base_dir():
    """Get the base directory: exe location (frozen) or project root (dev)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def setup_environment(base_dir):
    """Set environment variables for standalone mode."""
    os.chdir(base_dir)

    models_dir = os.path.join(base_dir, "models")
    static_dir = os.path.join(base_dir, "static")
    data_dir = os.path.join(base_dir, "data")
    uploads_dir = os.path.join(base_dir, "uploads")
    exports_dir = os.path.join(base_dir, "exports")

    for d in [data_dir, uploads_dir, exports_dir]:
        os.makedirs(d, exist_ok=True)

    env_file = os.path.join(base_dir, ".env")
    env_example = os.path.join(base_dir, ".env.example")
    if not os.path.exists(env_file) and os.path.exists(env_example):
        import shutil
        shutil.copy2(env_example, env_file)
        print("[启动器] 已从 .env.example 创建 .env，请编辑填写 API Key 后重新启动。")
        input("按回车键退出...")
        sys.exit(0)

    if not os.path.exists(env_file):
        print("[启动器] 错误: 未找到 .env 配置文件。")
        print("         请复制 .env.example 为 .env 并填写 LLM API Key。")
        input("按回车键退出...")
        sys.exit(1)

    defaults = {
        "INTERVIEW_STATIC_DIR": static_dir,
        "INTERVIEW_DATABASE_URL": f"sqlite:///{os.path.join(data_dir, 'interview.db')}",
        "INTERVIEW_UPLOAD_DIR": uploads_dir,
        "INTERVIEW_CORS_ORIGINS": '["http://localhost:8000"]',
    }

    if os.path.isdir(models_dir):
        paraformer_dir = _find_subdir(models_dir, "sherpa-onnx-streaming-paraformer")
        sensevoice_dir = _find_subdir(models_dir, "sherpa-onnx-sense-voice")
        punct_dir = _find_subdir(models_dir, "sherpa-onnx-punct")
        vad_file = os.path.join(models_dir, "silero_vad.onnx")
        speaker_file = os.path.join(models_dir, "3dspeaker.onnx")

        if paraformer_dir:
            defaults["INTERVIEW_ASR_MODEL_DIR"] = paraformer_dir
        if sensevoice_dir:
            defaults["INTERVIEW_ASR_OFFLINE_MODEL"] = os.path.join(sensevoice_dir, "model.int8.onnx")
            defaults["INTERVIEW_ASR_OFFLINE_TOKENS"] = os.path.join(sensevoice_dir, "tokens.txt")
        if punct_dir:
            defaults["INTERVIEW_PUNCT_MODEL_PATH"] = os.path.join(punct_dir, "model.int8.onnx")
        if os.path.isfile(vad_file):
            defaults["INTERVIEW_VAD_MODEL_PATH"] = vad_file
        if os.path.isfile(speaker_file):
            defaults["INTERVIEW_SPEAKER_MODEL_PATH"] = speaker_file

    for key, value in defaults.items():
        if key not in os.environ:
            os.environ[key] = value


def _find_subdir(parent, prefix):
    """Find first subdirectory starting with prefix."""
    if not os.path.isdir(parent):
        return None
    for name in os.listdir(parent):
        if name.startswith(prefix) and os.path.isdir(os.path.join(parent, name)):
            return os.path.join(parent, name)
    return None


def open_browser_delayed(url, delay=2.0):
    """Open browser after a short delay to let the server start."""
    def _open():
        time.sleep(delay)
        webbrowser.open(url)
    t = threading.Thread(target=_open, daemon=True)
    t.start()


def run_server(base_dir):
    """Start the uvicorn server."""
    host = "127.0.0.1"
    port = 8000
    url = f"http://localhost:{port}"

    print()
    print("=" * 50)
    print("       面试助手 v1.0.0")
    print("=" * 50)
    print()
    print(f"  访问地址: {url}")
    print()
    print("  使用方法:")
    print("    1. 创建岗位，上传候选人简历")
    print("    2. 生成面试问题，进入面试")
    print("    3. 点击「开始面试」→「启动音频」")
    print("    4. 面试结束后生成总结报告")
    print()
    print("  关闭此窗口即可停止服务")
    print("=" * 50)
    print()

    open_browser_delayed(url)

    backend_dir = os.path.join(base_dir, "backend") if not getattr(sys, "frozen", False) else base_dir

    if getattr(sys, "frozen", False):
        sys.path.insert(0, base_dir)

        import uvicorn
        uvicorn.run("app.main:app", host=host, port=port, log_level="info")
    else:
        sys.path.insert(0, backend_dir)

        import uvicorn
        uvicorn.run("app.main:app", host=host, port=port, log_level="info")


def main():
    base_dir = get_base_dir()
    setup_environment(base_dir)

    try:
        run_server(base_dir)
    except KeyboardInterrupt:
        print("\n[启动器] 正在关闭...")
    except Exception as e:
        print(f"\n[启动器] 启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")


if __name__ == "__main__":
    main()
