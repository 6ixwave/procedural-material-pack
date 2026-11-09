@echo off
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python "C:\Users\aleks\Downloads\earn-auto\blender_assets\render_leather_low.py" > "C:\Users\aleks\Downloads\earn-auto\blender_assets\leather2.log" 2>&1
exit /b %ERRORLEVEL%
