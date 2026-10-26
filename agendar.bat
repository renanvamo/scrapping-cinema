@echo off
chcp 65001 >nul
rem Cria a tarefa agendada "CinemaClassicos": roda todo dia as 00:00 e as 12:00.
rem Se o PC estiver desligado/dormindo no horario, roda assim que ligar.
set "DIR=%~dp0"
if "%DIR:~-1%"=="\" set "DIR=%DIR:~0,-1%"
set "PY="
for /f "delims=" %%i in ('where python 2^>nul') do (
  if not defined PY set "PY=%%i"
)
if not defined PY (
  echo Python nao encontrado no PATH. Instale o Python ou ajuste o PATH.
  pause
  exit /b 1
)
echo Python: %PY%
echo Pasta:  %DIR%
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$a = New-ScheduledTaskAction -Execute '%PY%' -Argument '-m cinema_classicos' -WorkingDirectory '%DIR%';" ^
  "$t = @((New-ScheduledTaskTrigger -Daily -At '00:00'), (New-ScheduledTaskTrigger -Daily -At '12:00'));" ^
  "$s = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 1);" ^
  "Register-ScheduledTask -TaskName 'CinemaClassicos' -Action $a -Trigger $t -Settings $s -Description 'Avisa sobre classicos em cartaz nos cinemas de SP' -Force | Out-Null;" ^
  "Get-ScheduledTask -TaskName 'CinemaClassicos' | Get-ScheduledTaskInfo | Select-Object NextRunTime | Format-List"
if errorlevel 1 (
  echo Falhou ao criar a tarefa.
  pause
  exit /b 1
)
echo.
echo Pronto! Tarefa "CinemaClassicos" criada (00:00 e 12:00 todos os dias).
echo Para testar agora:   schtasks /Run /TN CinemaClassicos
echo Para remover:        schtasks /Delete /TN CinemaClassicos /F
pause
