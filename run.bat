@echo off
setlocal
set PATH=C:\msys64\ucrt64\bin;C:\msys64\usr\bin;%PATH%
echo Iniciando MarkAtlas via MSYS2 GTK 3...
C:\msys64\ucrt64\bin\python.exe main.py %*
endlocal
