# conf-repository.Ps1
# =============================================================
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# region Functions

function Add-ToFile {
    param ([string]$FilePath, [string]$Value)
    if (-not (Test-Path $FilePath)) {
        New-Item -Path $FilePath -ItemType "file" -Value ""
    }
    $content = Get-Content $FilePath
    if ($content -notcontains $Value) {
        Add-Content -Path $FilePath -Value $Value
    }
} 

#endregion

# =============================================================

# region Pipeline Script

Write-Output "=== Configuring repository ==="

Write-Output "* Step 1: activating virtual environment"
python -m venv env > $null
.\env\Scripts\Activate.ps1 > $null

Write-Output "* Step 2: installing requirements"
pip install -r .\requirements.txt > $null
Add-ToFile -FilePath ".\.gitignore" -Value ".env/"
Add-ToFile -FilePath ".\.gitignore" -Value ".venv/"
Add-ToFile -FilePath ".\.gitignore" -Value "env/"
Add-ToFile -FilePath ".\.gitignore" -Value "__pycache__/"
Add-ToFile -FilePath ".\.gitignore" -Value "__pycache__/"
Add-ToFile -FilePath ".\.gitignore" -Value "__pycache__/*"
Add-ToFile -FilePath ".\.gitignore" -Value "*/__pycache__/*"
Add-ToFile -FilePath ".\.gitignore" -Value "build/"
Add-ToFile -FilePath ".\.gitignore" -Value "dist/"

Write-Output "* Step 3: Install pre-commit hooks"
pre-commit install
Add-ToFile -FilePath ".\.gitignore" -Value ".git/"

Write-Output "* Step 4: Testing pre-commit run"
pre-commit run --all-files

#endregion
