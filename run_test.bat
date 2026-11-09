@echo off
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python "%~dp0\test_one.py" > "%~dp0\test.log" 2>&1
exit /b %ERRORLEVEL%

