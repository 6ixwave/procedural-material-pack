@echo off
setlocal
set "BLENDER=C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
set "SCRIPT=%~dp0\render_one.py"
set "LOG=%~dp0\full_render.log"

echo === BLENDER MATERIAL BATCH: %date% %time% === > "%LOG%"

for %%M in (wood_oak wood_walnut brushed_steel copper concrete marble_white granite_gray leather_brown fabric_weave_red glass_clear gold_polished bark_oak) do (
    echo [%%M] starting... >> "%LOG%"
    "%BLENDER%" --background --python "%SCRIPT%" %%M >> "%LOG%" 2>&1
    echo [%%M] exit=%%ERRORLEVEL% >> "%LOG%"
)

echo === BATCH COMPLETE: %date% %time% === >> "%LOG%"

