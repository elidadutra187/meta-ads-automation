@echo off
chcp 65001 >nul
echo ============================================================
echo    INSTALADOR MCP - SALDAO CENTER
echo    Google Analytics, GTM, Meta Ads
echo ============================================================
echo.

REM Verificar se existe a pasta .claude
set CLAUDE_CONFIG_DIR=%USERPROFILE%\.claude
if not exist "%CLAUDE_CONFIG_DIR%" (
    echo Criando pasta de configuracao do Claude...
    mkdir "%CLAUDE_CONFIG_DIR%"
)

REM Copiar configuração MCP
echo Copiando configuracao MCP...
copy /Y "%~dp0mcp-config.json" "%CLAUDE_CONFIG_DIR%\mcp-config.json"

echo.
echo ============================================================
echo    CONFIGURACAO COPIADA COM SUCESSO!
echo ============================================================
echo.
echo MCPs configurados:
echo   - Meta Ads (Oficial Facebook)
echo   - Google Analytics 4 (Stape)
echo   - Google Tag Manager (Stape)
echo   - Stape Server
echo   - Saldao Local (Ollama)
echo.
echo ============================================================
echo    PROXIMOS PASSOS
echo ============================================================
echo.
echo 1. Reinicie o Claude Code
echo.
echo 2. Na primeira vez que usar cada MCP, voce sera
echo    redirecionado para fazer login:
echo.
echo    - Google Analytics: Login com conta Google
echo    - Google Tag Manager: Login com conta Google
echo    - Meta Ads: Login com conta Business Facebook
echo.
echo 3. Teste os comandos:
echo    "Liste minhas propriedades do GA4"
echo    "Quais tags tenho no GTM?"
echo    "Liste minhas campanhas do Meta Ads"
echo.
echo ============================================================
pause
