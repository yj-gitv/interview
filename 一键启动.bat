@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

title �������� - һ������

echo ============================================
echo        �������� - һ��������������
echo ============================================
echo.

:: ========== 1. ��� Docker �Ƿ�װ ==========
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo [����] δ��⵽ Docker�����Ȱ�װ Docker Desktop��
    echo.
    echo ���ص�ַ: https://www.docker.com/products/docker-desktop/
    echo ��װ���������ԣ�Ȼ���������д˽ű���
    echo.
    pause
    exit /b 1
)

:: ========== 2. ��� Docker �Ƿ����� ==========
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [��ʾ] Docker Desktop δ���У����ڳ�������...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe" 2>nul
    echo �ȴ� Docker �����У����Ժ�...
    :wait_docker
    timeout /t 5 /nobreak >nul
    docker info >nul 2>&1
    if %errorlevel% neq 0 (
        echo   ��������...
        goto wait_docker
    )
    echo [�ɹ�] Docker ��������
    echo.
)

:: ========== 3. �ж���Ŀ�ļ��Ƿ���� ==========
set "PROJECT_DIR=%~dp0"

if not exist "%PROJECT_DIR%docker-compose.yml" (
    echo [����] δ�ҵ� docker-compose.yml �ļ���
    echo ��ȷ���˽ű�������Ŀ�ļ����ڡ�
    echo.
    pause
    exit /b 1
)

echo [OK] ��Ŀ�ļ��Ѿ�����
echo.

:: ========== 4. ���� .env ==========
if not exist "%PROJECT_DIR%.env" (
    echo ============================================
    echo   �״����У���Ҫ���� API ��Ϣ
    echo ============================================
    echo.

    copy "%PROJECT_DIR%.env.example" "%PROJECT_DIR%.env" >nul 2>&1

    if not exist "%PROJECT_DIR%.env" (
        echo [����] �Ҳ��� .env.example �ļ����޷��������á�
        pause
        exit /b 1
    )

    echo ��������� LLM API Key�����:
    set /p "API_KEY="
    if "!API_KEY!"=="" (
        echo [����] API Key ����Ϊ�ա�
        pause
        exit /b 1
    )

    echo.
    echo ������ LLM API ��ַ��ֱ�ӻس�ʹ��Ĭ�� https://api.openai.com/v1��:
    set /p "BASE_URL="
    if "!BASE_URL!"=="" set "BASE_URL=https://api.openai.com/v1"

    :: д�� .env
    (
        echo # === ���� ===
        echo INTERVIEW_OPENAI_API_KEY=!API_KEY!
        echo INTERVIEW_OPENAI_BASE_URL=!BASE_URL!
        echo.
        echo # === ��ѡ��LLM ģ�� ===
        echo # INTERVIEW_OPENAI_MODEL_FAST=gpt-4o-mini
        echo # INTERVIEW_OPENAI_MODEL_STRONG=gpt-4o
        echo.
        echo # === ��ѡ������ʶ�� ===
        echo # INTERVIEW_WHISPER_MODEL=small
        echo.
        echo # === Docker �˿ڣ�Ĭ�� 3000��===
        echo # APP_PORT=3000
    ) > "%PROJECT_DIR%.env"

    echo.
    echo [�ɹ�] �����ѱ��档
    echo.
) else (
    echo [OK] �Ѽ�⵽ .env �����ļ���
    echo.
)

:: ========== 5. ���������� ==========
echo ============================================
echo   ���ڹ���������Ӧ��...
echo   �״�������Ҫ 10-20 ���ӣ������ĵȴ�
echo ============================================
echo.

cd /d "%PROJECT_DIR%"
docker compose up --build -d

if %errorlevel% neq 0 (
    echo.
    echo [����] ����ʧ�ܣ������Ϸ�������Ϣ��
    echo ����ԭ��
    echo   - Docker Desktop δ��ȫ����
    echo   - ������������
    echo   - �˿� 3000 ��ռ�ã����� .env ���޸� APP_PORT��
    echo.
    pause
    exit /b 1
)

:: ========== 6. �ȴ�������� ==========
echo.
echo �ȴ�����������...
timeout /t 10 /nobreak >nul

:: ========== 7. ������� ==========
echo.
echo ============================================
echo   �����ɹ������ڴ������...
echo ============================================
echo.
echo ���ʵ�ַ: http://localhost:3000
echo.
echo ��ʾ:
echo   - �رմ˴��ڲ���ֹͣ����
echo   - ֹͣ����: �ڴ��ļ��д��նˣ����� docker compose down
echo   - �鿴��־: docker compose logs -f
echo.

start http://localhost:3000

pause
