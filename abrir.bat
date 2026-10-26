@echo off
chcp 65001 >nul
rem Abre a pagina com os botoes "Buscar agora" e "Testar busca".
rem Deixe esta janela aberta enquanto usa a pagina; feche-a para parar.
cd /d "%~dp0"
python -m cinema_classicos --servidor
pause
