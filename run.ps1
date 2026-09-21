# Executa o MarkAtlas utilizando o runtime GTK 3 do MSYS2
$env:PATH = "C:\msys64\ucrt64\bin;C:\msys64\usr\bin;" + $env:PATH
Write-Host "Iniciando MarkAtlas via MSYS2 GTK 3..." -ForegroundColor Cyan
& C:\msys64\ucrt64\bin\python.exe main.py $args
