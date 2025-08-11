# Script PowerShell pour le debug de démarrage de Writing Tools
# Ce script capture des informations détaillées sur l'environnement de démarrage

param(
    [switch]$WaitForUser = $false,
    [int]$DelaySeconds = 0
)

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $ScriptDir "startup_logs"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $LogDir "powershell_debug_$Timestamp.log"

# Créer le dossier de logs
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Fonction de logging
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $LogEntry = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff') - $Level - $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry
}

# Début du script
Write-Log "========================================" 
Write-Log "WRITING TOOLS - POWERSHELL STARTUP DEBUG"
Write-Log "========================================"
Write-Log "Script started from: $ScriptDir"
Write-Log "Log file: $LogFile"

# Délai optionnel (utile pour le démarrage)
if ($DelaySeconds -gt 0) {
    Write-Log "Waiting $DelaySeconds seconds before starting..."
    Start-Sleep -Seconds $DelaySeconds
}

try {
    # Informations système
    Write-Log "=== SYSTEM INFORMATION ==="
    Write-Log "Computer Name: $env:COMPUTERNAME"
    Write-Log "User Name: $env:USERNAME"
    Write-Log "User Profile: $env:USERPROFILE"
    Write-Log "Current Directory: $(Get-Location)"
    Write-Log "PowerShell Version: $($PSVersionTable.PSVersion)"
    Write-Log "OS Version: $([System.Environment]::OSVersion.VersionString)"
    
    # Informations sur la session
    Write-Log "=== SESSION INFORMATION ==="
    $SessionInfo = Get-CimInstance -ClassName Win32_LogonSession | Where-Object { $_.LogonType -eq 2 } | Select-Object -First 1
    if ($SessionInfo) {
        Write-Log "Logon Type: Interactive"
        Write-Log "Start Time: $($SessionInfo.StartTime)"
    }
    
    # Vérifier les processus Writing Tools existants
    Write-Log "=== EXISTING PROCESSES ==="
    $ExistingProcesses = Get-Process | Where-Object { $_.ProcessName -like "*Writing*" -or $_.ProcessName -like "*main*" }
    if ($ExistingProcesses) {
        foreach ($proc in $ExistingProcesses) {
            Write-Log "Found process: $($proc.ProcessName) (PID: $($proc.Id))"
        }
    } else {
        Write-Log "No existing Writing Tools processes found"
    }
    
    # Vérifier l'état du système tray
    Write-Log "=== SYSTEM TRAY STATUS ==="
    $ExplorerProcess = Get-Process -Name "explorer" -ErrorAction SilentlyContinue
    if ($ExplorerProcess) {
        Write-Log "Explorer.exe is running (PID: $($ExplorerProcess.Id))"
        Write-Log "Explorer start time: $($ExplorerProcess.StartTime)"
    } else {
        Write-Log "WARNING: Explorer.exe not found!"
    }
    
    # Vérifier Python
    Write-Log "=== PYTHON ENVIRONMENT ==="
    try {
        $PythonVersion = & python --version 2>&1
        Write-Log "Python version: $PythonVersion"
        
        $PythonPath = & where python 2>&1
        Write-Log "Python path: $PythonPath"
    } catch {
        Write-Log "ERROR: Python not found or not accessible" "ERROR"
    }
    
    # Changer vers le répertoire du script
    Set-Location $ScriptDir
    Write-Log "Changed directory to: $(Get-Location)"
    
    # Lancer le script Python de debug
    Write-Log "=== LAUNCHING PYTHON DEBUG SCRIPT ==="
    Write-Log "Starting startup_debug.py..."
    
    $PythonProcess = Start-Process -FilePath "python" -ArgumentList "startup_debug.py" -NoNewWindow -PassThru -Wait
    
    Write-Log "Python script completed with exit code: $($PythonProcess.ExitCode)"
    
    if ($PythonProcess.ExitCode -eq 0) {
        Write-Log "Python debug script completed successfully"
    } else {
        Write-Log "Python debug script failed" "ERROR"
    }
    
} catch {
    Write-Log "CRITICAL ERROR: $($_.Exception.Message)" "ERROR"
    Write-Log "Stack trace: $($_.ScriptStackTrace)" "ERROR"
}

Write-Log "=== DEBUG SESSION COMPLETED ==="
Write-Log "Full log saved to: $LogFile"

# Attendre l'utilisateur si demandé
if ($WaitForUser) {
    Write-Log "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
