@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

title 面试助手 - 一键启动

echo ============================================
echo        面试助手 - 一键部署启动工具
echo ============================================
echo.

set "PROJECT_DIR=%~dp0"

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

:: ========== 2. 配置 .env ==========
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

:: ========== 3. 构建并启动容器 ==========
echo.
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
    pause
    exit /b 1
)

:: ========== 4. 打开浏览器 ==========
echo.
timeout /t 8 /nobreak >nul

echo ============================================
echo   启动成功！
echo ============================================
echo.
echo   访问地址: http://localhost:3000
echo   请使用 Chrome 浏览器打开
echo.
echo   使用方法:
echo     1. 创建岗位和候选人，进入面试页面
echo     2. 点击"开始面试"
echo     3. 点击"启动音频"
echo     4. 允许麦克风权限（录制你的声音）
echo     5. 选择"整个屏幕"并勾选"共享系统音频"
echo        （录制腾讯会议/Zoom 对方的声音）
echo     6. 开始面试，实时转录会自动出现
echo.
echo   提示：如果不需要录对方声音，第5步可以取消
echo.
echo ============================================
echo   按任意键停止服务...
echo ============================================

start http://localhost:3000

pause >nul

:: ========== 5. 停止 ==========
echo.
echo [停止] 正在关闭面试助手...
cd /d "%PROJECT_DIR%"
docker compose down

echo.
echo [OK] 已关闭。
pause
