$ErrorActionPreference = "Stop"
$version = "v3.4.17"
$bin = ".\tailwindcss.exe"
if (-not (Test-Path $bin)) {
    Write-Host "Baixando Tailwind CLI standalone $version..."
    Invoke-WebRequest -Uri "https://github.com/tailwindlabs/tailwindcss/releases/download/$version/tailwindcss-windows-x64.exe" -OutFile $bin
}
New-Item -ItemType Directory -Force -Path static\css | Out-Null
& $bin -i static_src\input.css -o static\css\tailwind.css --minify
Write-Host "CSS compilado em static/css/tailwind.css"
