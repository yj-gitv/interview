@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

set "VERSION=1.0.0"
set "PROJECT_DIR=%~dp0"
set "DIST_DIR=%PROJECT_DIR%dist\interview-assistant"
set "ZIP_NAME=面试助手-v%VERSION%-windows"

echo ============================================
echo   面试助手 v%VERSION% - 构建工具
echo ============================================
echo.

:: ========== 1. 检查依赖 ==========
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Node.js，请先安装。
    pause
    exit /b 1
)

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装。
    pause
    exit /b 1
)

python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 安装 PyInstaller...
    pip install pyinstaller
)

:: ========== 2. 构建前端 ==========
echo.
echo [1/4] 构建前端...
cd /d "%PROJECT_DIR%frontend"
call npm ci --silent
if %errorlevel% neq 0 (
    echo [错误] npm ci 失败
    pause
    exit /b 1
)
call npm run build
if %errorlevel% neq 0 (
    echo [错误] 前端构建失败
    pause
    exit /b 1
)
echo [OK] 前端构建完成

:: ========== 3. PyInstaller 打包后端 ==========
echo.
echo [2/4] 打包后端（PyInstaller）...
cd /d "%PROJECT_DIR%"
pyinstaller --noconfirm interview.spec
if %errorlevel% neq 0 (
    echo [错误] PyInstaller 打包失败
    pause
    exit /b 1
)
echo [OK] 后端打包完成

:: ========== 4. 组装发布包 ==========
echo.
echo [3/4] 组装发布包...

:: Copy frontend build output
if exist "%DIST_DIR%\static" rmdir /s /q "%DIST_DIR%\static"
xcopy /e /i /q "%PROJECT_DIR%frontend\dist" "%DIST_DIR%\static" >nul

:: Create data directories
mkdir "%DIST_DIR%\data" 2>nul
mkdir "%DIST_DIR%\uploads" 2>nul
mkdir "%DIST_DIR%\exports" 2>nul

:: Create models directory (user needs to download models separately)
mkdir "%DIST_DIR%\models" 2>nul

:: Copy .env.example
copy "%PROJECT_DIR%.env.example" "%DIST_DIR%\.env.example" >nul

:: Create README for the release
(
    echo ============================================
    echo   面试助手 v%VERSION% - 使用说明
    echo ============================================
    echo.
    echo 【快速开始】
    echo.
    echo   1. 复制 .env.example 为 .env
    echo   2. 编辑 .env，填写你的 LLM API Key
    echo   3. 双击"面试助手.exe"启动
    echo   4. 浏览器会自动打开 http://localhost:3000
    echo.
    echo 【语音识别模型（可选）】
    echo.
    echo   如需启用实时语音转录，请下载以下模型文件到 models 目录：
    echo.
    echo   - sherpa-onnx-streaming-paraformer-bilingual-zh-en/  （实时流式识别）
    echo     https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-streaming-paraformer-bilingual-zh-en.tar.bz2
    echo.
    echo   - sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17/  （离线高精度识别）
    echo     https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17.tar.bz2
    echo.
    echo   - sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12-int8/  （标点恢复）
    echo     https://github.com/k2-fsa/sherpa-onnx/releases/download/punctuation-models/sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12-int8.tar.bz2
    echo.
    echo   - silero_vad.onnx  （语音检测）
    echo     https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx
    echo.
    echo   - 3dspeaker.onnx  （说话人识别）
    echo     https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx
    echo.
    echo   不下载模型也可以使用，但只能用手动输入模式。
    echo.
    echo 【停止服务】
    echo.
    echo   关闭控制台窗口即可。
    echo.
    echo 【数据说明】
    echo.
    echo   - data/     数据库文件
    echo   - uploads/  上传的简历文件
    echo   - exports/  导出的 PDF 文件
    echo   - models/   语音识别模型
    echo.
) > "%DIST_DIR%\使用说明.txt"

echo [OK] 发布包组装完成

:: ========== 5. 压缩 ==========
echo.
echo [4/4] 创建压缩包...
cd /d "%PROJECT_DIR%dist"
if exist "%ZIP_NAME%.zip" del "%ZIP_NAME%.zip"
powershell -command "Compress-Archive -Path 'interview-assistant\*' -DestinationPath '%ZIP_NAME%.zip' -Force"
if %errorlevel% neq 0 (
    echo [警告] 压缩失败，请手动压缩 dist\interview-assistant 目录
) else (
    echo [OK] 压缩包已创建: dist\%ZIP_NAME%.zip
)

echo.
echo ============================================
echo   构建完成！
echo ============================================
echo.
echo   发布目录: %DIST_DIR%
echo   压缩包:   %PROJECT_DIR%dist\%ZIP_NAME%.zip
echo.
echo   测试运行: 双击 dist\interview-assistant\面试助手.exe
echo.
pause
