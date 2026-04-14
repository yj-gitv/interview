@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

title 面试助手 - 一键启动

echo ============================================
echo        面试助手 - 一键部署启动工具
echo ============================================
echo.

set "PROJECT_DIR=%~dp0"
set "SCRIPTS_DIR=%PROJECT_DIR%scripts\"

:: ========== 1. 检查 Docker ==========
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Docker，请先安装 Docker Desktop。
    echo        下载: https://www.docker.com/products/docker-desktop/
    echo        安装后重启电脑，再运行此脚本。
    echo.
    pause
    exit /b 1
)

docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] Docker Desktop 未运行，正在启动...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe" 2>nul
    :wait_docker
    timeout /t 5 /nobreak >nul
    docker info >nul 2>&1
    if %errorlevel% neq 0 (
        echo   还在启动...
        goto wait_docker
    )
    echo [OK] Docker 已启动。
    echo.
)

:: ========== 2. 检查 VoiceMeeter ==========
echo [检查] 音频虚拟设备 VoiceMeeter...

powershell -ExecutionPolicy Bypass -File "%SCRIPTS_DIR%audio-setup.ps1" -Action check >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ============================================
    echo   需要安装 VoiceMeeter（免费音频虚拟设备）
    echo   用于采集腾讯会议等视频通话中双方的声音
    echo ============================================
    echo.
    echo 正在下载 VoiceMeeter 安装包...

    powershell -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://download.vb-audio.com/Download_CABLE/VoicemeeterSetup_v1122.zip' -OutFile '%TEMP%\VoicemeeterSetup.zip'"
    if %errorlevel% neq 0 (
        echo [错误] 下载失败，请手动下载: https://voicemeeter.com
        pause
        exit /b 1
    )

    echo 正在解压...
    powershell -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%TEMP%\VoicemeeterSetup.zip' -DestinationPath '%TEMP%\VoicemeeterSetup' -Force"

    echo.
    echo ================================================
    echo   即将弹出 VoiceMeeter 安装程序
    echo   请点击 Install，安装完成后【重启电脑】
    echo   重启后再次双击此脚本即可
    echo ================================================
    echo.
    start /wait "" "%TEMP%\VoicemeeterSetup\voicemeetersetup.exe"

    echo.
    echo 安装完成，请重启电脑后再次运行此脚本。
    pause
    exit /b 0
) else (
    echo [OK] VoiceMeeter 已安装。
)
echo.

:: ========== 3. 配置 .env ==========
if not exist "%PROJECT_DIR%.env" (
    echo ============================================
    echo   首次运行，需要配置 API 信息
    echo ============================================
    echo.

    copy "%PROJECT_DIR%.env.example" "%PROJECT_DIR%.env" >nul 2>&1

    if not exist "%PROJECT_DIR%.env" (
        echo [错误] 找不到 .env.example 文件。
        pause
        exit /b 1
    )

    echo 请输入你的 LLM API Key（必填）:
    set /p "API_KEY="
    if "!API_KEY!"=="" (
        echo [错误] API Key 不能为空。
        pause
        exit /b 1
    )

    echo.
    echo 请输入 LLM API 地址（直接回车使用默认 https://api.openai.com/v1）:
    set /p "BASE_URL="
    if "!BASE_URL!"=="" set "BASE_URL=https://api.openai.com/v1"

    (
        echo # === 必填 ===
        echo INTERVIEW_OPENAI_API_KEY=!API_KEY!
        echo INTERVIEW_OPENAI_BASE_URL=!BASE_URL!
        echo.
        echo # === 可选 ===
        echo # INTERVIEW_WHISPER_MODEL=small
        echo # APP_PORT=3000
    ) > "%PROJECT_DIR%.env"

    echo.
    echo [OK] 配置已保存。
    echo.
) else (
    echo [OK] 已检测到 .env 配置文件。
)

:: ========== 4. 自动配置音频 ==========
echo.
echo [音频] 正在配置 VoiceMeeter 音频路由...
powershell -ExecutionPolicy Bypass -File "%SCRIPTS_DIR%audio-setup.ps1" -Action setup
echo.

:: ========== 5. 构建并启动容器 ==========
echo ============================================
echo   正在启动面试助手...
echo   首次启动需要 10-20 分钟，请耐心等待
echo ============================================
echo.

cd /d "%PROJECT_DIR%"
docker compose up --build -d

if %errorlevel% neq 0 (
    echo.
    echo [错误] 启动失败，请检查上方错误信息。
    echo.
    :: Restore audio before exit
    powershell -ExecutionPolicy Bypass -File "%SCRIPTS_DIR%audio-setup.ps1" -Action restore
    pause
    exit /b 1
)

:: ========== 6. 等待就绪并打开浏览器 ==========
echo.
timeout /t 8 /nobreak >nul

echo ============================================
echo   启动成功！
echo ============================================
echo.
echo   访问地址: http://localhost:3000
echo.
echo   使用方法:
echo     1. 打开腾讯会议/Zoom 开始面试
echo     2. 在面试助手中点"开始面试"
echo     3. 在"启动音频"旁的下拉框选择
echo        "VoiceMeeter Out B1"
echo     4. 点击"启动音频"即可录制双方声音
echo.
echo   音频已自动配置，退出后将自动恢复。
echo.
echo ============================================
echo   按任意键停止服务并恢复音频设置...
echo ============================================

start http://localhost:3000

pause >nul

:: ========== 7. 停止并恢复 ==========
echo.
echo [停止] 正在关闭面试助手...
cd /d "%PROJECT_DIR%"
docker compose down

echo [音频] 正在恢复原始音频设置...
powershell -ExecutionPolicy Bypass -File "%SCRIPTS_DIR%audio-setup.ps1" -Action restore

echo.
echo [OK] 已全部关闭，音频设置已恢复。
pause
