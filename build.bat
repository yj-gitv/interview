@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

title 面试助手 - 构建发布包

echo ============================================
echo        面试助手 - 构建发布包
echo ============================================
echo.

set "PROJECT_DIR=%~dp0"
set "VERSION=1.0.0"
set "DIST_NAME=面试助手"
set "DIST_DIR=%PROJECT_DIR%dist\%DIST_NAME%"

:: ========== 1. 检查依赖 ==========
echo [1/5] 检查构建依赖...

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Node.js，请先安装: https://nodejs.org/
    pause
    exit /b 1
)

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.11+
    pause
    exit /b 1
)

python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 正在安装 PyInstaller...
    pip install pyinstaller
)

echo [OK] 依赖检查通过
echo.

:: ========== 2. 构建前端 ==========
echo [2/5] 构建前端...
cd /d "%PROJECT_DIR%frontend"
call npm ci
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
echo.

:: ========== 3. PyInstaller 打包 ==========
echo [3/5] 打包后端...
cd /d "%PROJECT_DIR%"
python -m PyInstaller interview.spec --noconfirm
if %errorlevel% neq 0 (
    echo [错误] PyInstaller 打包失败
    pause
    exit /b 1
)
echo [OK] 后端打包完成
echo.

:: ========== 4. 组装发布包 ==========
echo [4/5] 组装发布包...

:: Copy frontend build output
if exist "%DIST_DIR%\static" rmdir /s /q "%DIST_DIR%\static"
xcopy /e /i /q "%PROJECT_DIR%frontend\dist" "%DIST_DIR%\static" >nul

:: Create empty directories
if not exist "%DIST_DIR%\data" mkdir "%DIST_DIR%\data"
if not exist "%DIST_DIR%\uploads" mkdir "%DIST_DIR%\uploads"
if not exist "%DIST_DIR%\exports" mkdir "%DIST_DIR%\exports"
if not exist "%DIST_DIR%\models" mkdir "%DIST_DIR%\models"

:: Copy .env.example
copy "%PROJECT_DIR%.env.example" "%DIST_DIR%\.env.example" >nul

:: Create README for end users
(
    echo ============================================
    echo        面试助手 v%VERSION% 使用说明
    echo ============================================
    echo.
    echo 一、首次使用
    echo.
    echo   1. 将 .env.example 复制并重命名为 .env
    echo   2. 用记事本打开 .env，填写你的 LLM API Key
    echo   3. 双击「面试助手.exe」启动
    echo   4. 浏览器会自动打开 http://localhost:8000
    echo.
    echo 二、语音识别模型（可选）
    echo.
    echo   如需实时语音转录功能，请下载模型文件放入 models 文件夹:
    echo.
    echo   - sherpa-onnx-streaming-paraformer-bilingual-zh-en/  （实时流式识别）
    echo   - sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17/  （离线精确识别）
    echo   - sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12-int8/  （标点恢复）
    echo   - silero_vad.onnx  （语音活动检测）
    echo   - 3dspeaker.onnx  （说话人识别）
    echo.
    echo   下载地址: https://github.com/k2-fsa/sherpa-onnx/releases
    echo.
    echo   即使没有模型文件，手动输入转录和 AI 总结功能也可以正常使用。
    echo.
    echo 三、日常使用
    echo.
    echo   双击「面试助手.exe」即可，关闭命令行窗口即停止服务。
    echo   面试数据保存在 data 文件夹中。
    echo.
) > "%DIST_DIR%\使用说明.txt"

echo [OK] 发布包组装完成
echo.

:: ========== 5. 压缩 ==========
echo [5/5] 压缩发布包...
cd /d "%PROJECT_DIR%dist"

:: Try PowerShell compression
powershell -NoProfile -Command "Compress-Archive -Path '.\%DIST_NAME%\*' -DestinationPath '.\%DIST_NAME%-v%VERSION%-windows.zip' -Force" 2>nul
if %errorlevel% equ 0 (
    echo [OK] 已生成: dist\%DIST_NAME%-v%VERSION%-windows.zip
) else (
    echo [提示] 自动压缩失败，请手动压缩 dist\%DIST_NAME% 文件夹
)

echo.
echo ============================================
echo   构建完成！
echo ============================================
echo.
echo   发布包位置: dist\%DIST_NAME%\
echo   压缩包:     dist\%DIST_NAME%-v%VERSION%-windows.zip
echo.
echo   测试方法: 进入 dist\%DIST_NAME%\ 双击 面试助手.exe
echo.
pause
