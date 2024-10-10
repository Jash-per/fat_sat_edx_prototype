# conf-repository.Ps1
# =============================================================


# region Functions

function Add-ToFile {
    param ([string]$file_path, [string]$value)
    if (!Test-Path $file_path) {
        Write-Output " file not found"
        return False
    }
    $content = Get-Content $file_path
    if ($content -notcontains $value) {
        Add-Content $file_path $value
    }
    return True
} 

#endregion

# =============================================================


# region Pipeline Script

Write-Output "=== Configuring repository ==="
Write-Output "* Step 1: activating virtual environment:"
python -m venv env
.\env\Scripts\Activate.ps1
Write-Output "* Step 2: installing requirements:"
pip install -r .\requirements.txt
Add-ToFile ".\.gitignore", ".env/"
Add-ToFile ".\.gitignore", ".venv/"
Add-ToFile ".\.gitignore", "env/"
Write-Output "* Step 3: Install pre-commit hooks:"
pre-commit install
# Also add .git directory to .git-ignore
Add-ToFile ".\.gitignore", ".git/"
Write-Output "* Step 4: Testing pre-commit run"
pre-commit run --all-files

#endregion
