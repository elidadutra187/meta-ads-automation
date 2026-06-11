@echo off
chcp 65001 >nul
echo Instalando configuracao MCP no Claude Desktop...

set "CONFIG_DIR=%APPDATA%\Claude"
set "CONFIG_FILE=%CONFIG_DIR%\claude_desktop_config.json"

if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"

(
echo {
echo   "mcpServers": {
echo     "composio-saldao": {
echo       "url": "https://mcp.composio.dev/saldao-center/ak_F86dMTnyUmU68-zYFM5i"
echo     },
echo     "meta-ads": {
echo       "url": "https://mcp.facebook.com/ads"
echo     },
echo     "google-analytics": {
echo       "url": "https://mcp-ga.stape.ai/mcp"
echo     },
echo     "google-tag-manager": {
echo       "url": "https://mcp-gtm.stape.ai/mcp"
echo     }
echo   }
echo }
) > "%CONFIG_FILE%"

echo.
echo Configuracao salva em:
echo %CONFIG_FILE%
echo.
echo Conteudo:
type "%CONFIG_FILE%"
echo.
echo ========================================
echo PRONTO! Agora:
echo 1. Feche o Claude Desktop completamente
echo 2. Abra novamente
echo 3. Quando pedir algo, ele vai pedir para autorizar cada servico
echo ========================================
pause
