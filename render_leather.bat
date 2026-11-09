@echo off
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python "%~dp0\render_one.py" leather_brown > "%~dp0\leather.log" 2>&1
exit /b %ERRORLEVEL%

