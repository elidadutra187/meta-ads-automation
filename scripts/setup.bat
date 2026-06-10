@echo off
echo ========================================
echo Meta Ads Automation - Setup
echo ========================================
echo.

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    echo Instale Python 3.9+ de https://python.org
    pause
    exit /b 1
)
echo [OK] Python encontrado

REM Criar ambiente virtual
echo.
echo Criando ambiente virtual...
python -m venv venv
call venv\Scripts\activate.bat

REM Instalar dependencias
echo.
echo Instalando dependencias...
pip install -r requirements.txt

REM Criar .env se nao existir
if not exist .env (
    echo.
    echo Criando arquivo .env...
    copy .env.example .env
    echo [IMPORTANTE] Edite o arquivo .env com suas credenciais!
)

REM Verificar Ollama
echo.
echo Verificando Ollama...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [AVISO] Ollama nao encontrado!
    echo Instale de https://ollama.com
    echo.
) else (
    echo [OK] Ollama encontrado
    echo Baixando modelo llama3.2...
    ollama pull llama3.2
)

echo.
echo ========================================
echo Setup concluido!
echo ========================================
echo.
echo Proximos passos:
echo 1. Edite o arquivo .env com suas credenciais Meta
echo 2. Coloque seus criativos na pasta /criativos
echo 3. Execute: python -m src.main status
echo.
pause
