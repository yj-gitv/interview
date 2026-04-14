@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

title 面试助手 - 一键启动

echo ============================================
echo        面试助手 - 一键部署启动工具
echo ============================================
echo.

:: ========== 1. 检查 Docker 是否安装 ==========
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Docker，请先安装 Docker Desktop。
    echo.
    echo 下载地址: https://www.docker.com/products/docker-desktop/
    echo 安装后重启电脑，然后重新运行此脚本。
    echo.
    pause
    exit /b 1
)

:: ========== 2. 检查 Docker 是否运行 ==========
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] Docker Desktop 未运行，正在尝试启动...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe" 2>nul
    echo 等待 Docker 启动中，请稍候...
    :wait_docker
    timeout /t 5 /nobreak >nul
    docker info >nul 2>&1
    if %errorlevel% neq 0 (
        echo   还在启动...
        goto wait_docker
    )
    echo [成功] Docker 已启动。
    echo.
)

:: ========== 3. 判断项目文件是否存在 ==========
set "PROJECT_DIR=%~dp0"

if not exist "%PROJECT_DIR%docker-compose.yml" (
    echo [错误] 未找到 docker-compose.yml 文件。
    echo 请确保此脚本放在项目文件夹内。
    echo.
    pause
    exit /b 1
)

echo [OK] 项目文件已就绪。
echo.

:: ========== 4. 配置 .env ==========
if not exist "%PROJECT_DIR%.env" (
    echo ============================================
    echo   首次运行，需要配置 API 信息
    echo ============================================
    echo.

    copy "%PROJECT_DIR%.env.example" "%PROJECT_DIR%.env" >nul 2>&1

    if not exist "%PROJECT_DIR%.env" (
        echo [错误] 找不到 .env.example 文件，无法生成配置。
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

    :: 写入 .env
    (
        echo # === 必填 ===
        echo INTERVIEW_OPENAI_API_KEY=!API_KEY!
        echo INTERVIEW_OPENAI_BASE_URL=!BASE_URL!
        echo.
        echo # === 可选：LLM 模型 ===
        echo # INTERVIEW_OPENAI_MODEL_FAST=gpt-4o-mini
        echo # INTERVIEW_OPENAI_MODEL_STRONG=gpt-4o
        echo.
        echo # === 可选：语音识别 ===
        echo # INTERVIEW_WHISPER_MODEL=small
        echo.
        echo # === Docker 端口（默认 3000）===
        echo # APP_PORT=3000
    ) > "%PROJECT_DIR%.env"

    echo.
    echo [成功] 配置已保存。
    echo.
) else (
    echo [OK] 已检测到 .env 配置文件。
    echo.
)

:: ========== 5. 构建并启动 ==========
echo ============================================
echo   正在构建并启动应用...
echo   首次启动需要 10-20 分钟，请耐心等待
echo ============================================
echo.

cd /d "%PROJECT_DIR%"
docker compose up --build -d

if %errorlevel% neq 0 (
    echo.
    echo [错误] 启动失败，请检查上方错误信息。
    echo 常见原因：
    echo   - Docker Desktop 未完全启动
    echo   - 网络连接问题
    echo   - 端口 3000 被占用（可在 .env 中修改 APP_PORT）
    echo.
    pause
    exit /b 1
)

:: ========== 6. 等待服务就绪 ==========
echo.
echo 等待服务启动中...
timeout /t 10 /nobreak >nul

:: ========== 7. 打开浏览器 ==========
echo.
echo ============================================
echo   启动成功！正在打开浏览器...
echo ============================================
echo.
echo 访问地址: http://localhost:3000
echo.
echo 提示:
echo   - 关闭此窗口不会停止服务
echo   - 停止服务: 在此文件夹打开终端，输入 docker compose down
echo   - 查看日志: docker compose logs -f
echo.

start http://localhost:3000

pause
