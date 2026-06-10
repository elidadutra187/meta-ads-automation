@echo off
chcp 65001 >nul
echo ========================================
echo SALDAO CENTER - INSTALACAO MCP HUB
echo ========================================
echo.

REM Verificar Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [AVISO] Node.js nao encontrado!
    echo Instale de: https://nodejs.org
    echo.
)

REM Instalar MCPs via NPM
echo Instalando MCPs...
call npm install -g @mcpmarket/olist-erp 2>nul
call npm install -g @anthropic-ai/mcp 2>nul

REM Criar pasta de config do Claude Desktop
set CLAUDE_CONFIG=%APPDATA%\Claude
if not exist "%CLAUDE_CONFIG%" mkdir "%CLAUDE_CONFIG%"

REM Copiar configuracao
echo.
echo Configurando Claude Desktop...
copy /Y "claude_desktop_config.json" "%CLAUDE_CONFIG%\claude_desktop_config.json"

echo.
echo ========================================
echo INSTALACAO CONCLUIDA!
echo ========================================
echo.
echo Proximos passos:
echo 1. Edite o arquivo .env com suas credenciais
echo 2. Reinicie o Claude Desktop
echo 3. As ferramentas estarao disponiveis automaticamente
echo.
echo Credenciais necessarias:
echo - TINY_TOKEN (Tiny ERP)
echo - MULTIGROW_API_KEY (Multigrow CRM)
echo - META_ACCESS_TOKEN (Meta Ads)
echo - GTM_CONTAINER_ID (Google Tag Manager)
echo - GA4_PROPERTY_ID (Google Analytics)
echo.
pause
