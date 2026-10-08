@echo off
setlocal
chcp 65001 > nul
cd /d "%~dp0"
title Sever Store

echo.
echo  =============================================
echo   Sever Store: автоматический запуск проекта
echo  =============================================
echo.

set "PYTHON="
where py >nul 2>nul
if not errorlevel 1 set "PYTHON=py -3"
if defined PYTHON goto :python_ready

where python >nul 2>nul
if not errorlevel 1 set "PYTHON=python"
if defined PYTHON goto :python_ready

where winget >nul 2>nul
if errorlevel 1 goto :python_missing

echo  Python не найден. Устанавливаю автоматически...
winget install --id Python.Python.3.12 -e --source winget --scope user --silent --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto :python_missing

for /d %%D in ("%LocalAppData%\Programs\Python\Python3*") do (
    if exist "%%~fD\python.exe" set "PYTHON=%%~fD\python.exe"
)
if not defined PYTHON goto :python_missing

:python_ready
if not exist ".venv\Scripts\python.exe" (
    echo  [1/3] Создание локального окружения...
    call %PYTHON% -m venv ".venv"
    if errorlevel 1 goto :error
) else (
    echo  [1/3] Локальное окружение найдено.
)

echo  [2/3] Установка и проверка библиотек...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r "backend\requirements.txt"
if errorlevel 1 goto :error

echo  [3/3] Запуск сайта...
echo.
echo  Сайт: http://127.0.0.1:8000
echo  API:  http://127.0.0.1:8000/docs
echo.
echo  При первом запуске установка может занять несколько минут.
echo  Не закрывайте это окно. Для остановки нажмите Ctrl+C.
echo.

start "" /b powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8000'"
".venv\Scripts\python.exe" -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
exit /b 0

:python_missing
echo.
echo  Не удалось автоматически установить Python.
echo  Установите Python: https://www.python.org/downloads/
start "" "https://www.python.org/downloads/"
pause
exit /b 1

:error
echo.
echo  Не удалось подготовить проект. Проверьте подключение к интернету.
pause
exit /b 1