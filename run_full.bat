@echo off
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python "%~dp0\generate_assets.py" > "%~dp0\full_render.log" 2>&1
exit /b %ERRORLEVEL%

