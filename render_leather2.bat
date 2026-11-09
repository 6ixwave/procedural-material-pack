@echo off
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python "%~dp0\render_leather_low.py" > "%~dp0\leather2.log" 2>&1
exit /b %ERRORLEVEL%

