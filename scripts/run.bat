@echo off
echo Meta Ads Automation
echo.

REM Ativar ambiente virtual
call venv\Scripts\activate.bat 2>nul

REM Verificar argumentos
if "%1"=="" (
    echo Comandos disponiveis:
    echo   run status        - Verificar conexoes
    echo   run listar        - Listar campanhas
    echo   run upload        - Upload de criativos
    echo   run gerar-copy    - Gerar copy com IA
    echo   run criar         - Criar campanha completa
    echo   run insights ID   - Ver metricas
    echo   run otimizar      - Otimizar campanhas
    echo   run monitorar     - Iniciar monitoramento
    echo   run relatorio     - Gerar relatorio
    echo.
    echo Exemplo: run criar "Meu Produto" "https://meusite.com"
    goto :eof
)

python -m src.main %*
