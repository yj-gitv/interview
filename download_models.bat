@echo off
chcp 65001 >nul 2>&1
setlocal

title 面试助手 - 下载语音识别模型

echo ============================================
echo   面试助手 - 下载语音识别模型
echo ============================================
echo.
echo   模型总大小约 400MB，下载时间取决于网速。
echo   如果不需要实时语音转录，可以跳过此步骤。
echo.

set "MODELS_DIR=%~dp0models"
if not exist "%MODELS_DIR%" mkdir "%MODELS_DIR%"
cd /d "%MODELS_DIR%"

echo [1/5] 下载流式语音识别模型 (Paraformer, ~226MB)...
curl -sL --retry 5 --retry-delay 3 -o paraformer.tar.bz2 ^
    https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-streaming-paraformer-bilingual-zh-en.tar.bz2
if %errorlevel% equ 0 (
    tar xjf paraformer.tar.bz2
    del paraformer.tar.bz2
    echo [OK] Paraformer 模型下载完成
) else (
    echo [警告] Paraformer 下载失败，请稍后重试
)
echo.

echo [2/5] 下载离线语音识别模型 (SenseVoice, ~70MB)...
curl -sL --retry 5 --retry-delay 3 -o sensevoice.tar.bz2 ^
    https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17.tar.bz2
if %errorlevel% equ 0 (
    tar xjf sensevoice.tar.bz2
    del sensevoice.tar.bz2
    echo [OK] SenseVoice 模型下载完成
) else (
    echo [警告] SenseVoice 下载失败，请稍后重试
)
echo.

echo [3/5] 下载标点恢复模型 (~63MB)...
curl -sL --retry 5 --retry-delay 3 -o punct.tar.bz2 ^
    https://github.com/k2-fsa/sherpa-onnx/releases/download/punctuation-models/sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12-int8.tar.bz2
if %errorlevel% equ 0 (
    tar xjf punct.tar.bz2
    del punct.tar.bz2
    echo [OK] 标点恢复模型下载完成
) else (
    echo [警告] 标点恢复模型下载失败，请稍后重试
)
echo.

echo [4/5] 下载语音活动检测模型 (Silero VAD, ~2MB)...
curl -sL --retry 5 --retry-delay 3 -o silero_vad.onnx ^
    https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx
if %errorlevel% equ 0 (
    echo [OK] VAD 模型下载完成
) else (
    echo [警告] VAD 模型下载失败，请稍后重试
)
echo.

echo [5/5] 下载说话人识别模型 (3D-Speaker, ~26MB)...
curl -sL --retry 5 --retry-delay 3 -o 3dspeaker.onnx ^
    https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx
if %errorlevel% equ 0 (
    echo [OK] 说话人识别模型下载完成
) else (
    echo [警告] 说话人识别模型下载失败，请稍后重试
)

echo.
echo ============================================
echo   模型下载完成！
echo ============================================
echo.
echo   模型已保存到: %MODELS_DIR%
echo   现在可以启动面试助手并使用实时语音转录功能。
echo.
pause
