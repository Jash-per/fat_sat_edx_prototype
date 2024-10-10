.\env\Scripts\activate.ps1

# Run pre-commit to test
pre-commit run --all-files

$BuildPath = "./build"

if (-not (Test-Path -Path $BuildPath)) {
    New-Item -ItemType Directory -Path $BuildPath
}
# If integration procedures are successful build the executable using pyinstaller
if($LASTEXITCODE -eq 0) {
    pyinstaller -p $BuildPath --name fat_sat_edx_prototype --onefile --windowed main.py
}
