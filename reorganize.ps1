# Reorganize notebooks into multiple cells and update in Fabric

param(
    [Parameter(Mandatory = $true)][string]$WorkspaceName,
    [string]$LakehouseName = "nba_lakehouse"
)

$ErrorActionPreference = "Stop"

# Get token
Write-Host "Getting authentication token..." -ForegroundColor Yellow
$TokenResponse = az account get-access-token --resource "https://api.fabric.microsoft.com" | ConvertFrom-Json
$Token = $TokenResponse.accessToken

# Get workspace ID
Write-Host "Finding workspace..." -ForegroundColor Yellow
$Url = "https://api.fabric.microsoft.com/v1/workspaces"
$Headers = @{
    "Authorization" = "Bearer $Token"
    "x-ms-fabric-skill" = "spark-cli"
    "Content-Type" = "application/json"
}

$Workspaces = Invoke-RestMethod -Uri $Url -Method GET -Headers $Headers
$Workspace = $Workspaces.value | Where-Object { $_.displayName -eq $WorkspaceName }
$WorkspaceId = $Workspace.id
Write-Host "Workspace ID: $WorkspaceId" -ForegroundColor Green

# Get lakehouse ID
Write-Host "Finding lakehouse..." -ForegroundColor Yellow
$Url = "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/items?type=Lakehouse"
$Items = Invoke-RestMethod -Uri $Url -Method GET -Headers $Headers
$Lakehouse = $Items.value | Where-Object { $_.displayName -eq $LakehouseName }
$LakehouseId = $Lakehouse.id
Write-Host "Lakehouse ID: $LakehouseId" -ForegroundColor Green
Write-Host ""

# Function to parse cells
function Parse-NotebookCells {
    param([string]$SourceCode)
    
    $lines = $SourceCode -split "`n"
    $cells = @()
    $currentCell = @()
    $cellMarkerPattern = "^# Cell \d+:"
    $separatorPattern = "^# ={10,}"
    
    foreach ($line in $lines) {
        # Check if this is a cell marker
        if ($line -match $cellMarkerPattern) {
            # Save previous cell if it has content
            $cellContent = ($currentCell | ForEach-Object { $_ }) -join "`n"
            $cellContent = $cellContent.Trim()
            
            if ($cellContent -and $cellContent -ne "" -and $cellContent -notmatch "^# ={10,}$") {
                $cells += $cellContent
            }
            
            $currentCell = @()
            $currentCell += $line
        } else {
            $currentCell += $line
        }
    }
    
    # Add final cell
    $cellContent = ($currentCell | ForEach-Object { $_ }) -join "`n"
    $cellContent = $cellContent.Trim()
    if ($cellContent) {
        $cells += $cellContent
    }
    
    # Filter empty cells
    $cells = $cells | Where-Object { $_.Trim() -and $_.Trim() -ne "# ============================================" }
    
    return $cells
}

# Function to create notebook JSON with multiple cells
function Create-MultiCellNotebook {
    param(
        [string[]]$Cells,
        [string]$LakehouseId,
        [string]$WorkspaceId,
        [string]$LakehouseName
    )
    
    $NotebookCells = @()
    
    foreach ($CellSource in $Cells) {
        # Format source lines
        $SourceLines = $CellSource -split "`n"
        $FormattedSource = @()
        
        for ($i = 0; $i -lt $SourceLines.Count - 1; $i++) {
            $FormattedSource += $SourceLines[$i] + "`n"
        }
        
        if ($SourceLines[-1]) {
            $FormattedSource += $SourceLines[-1]
        }
        
        $NotebookCells += @{
            cell_type = "code"
            execution_count = $null
            metadata = @{}
            outputs = @()
            source = $FormattedSource
        }
    }
    
    $Notebook = @{
        cells = $NotebookCells
        metadata = @{
            kernelspec = @{
                display_name = "Python 3"
                language = "python"
                name = "python3"
            }
            language_info = @{
                name = "python"
                version = "3.11"
            }
            dependencies = @{
                lakehouse = @{
                    default_lakehouse = $LakehouseId
                    default_lakehouse_workspace_id = $WorkspaceId
                    default_lakehouse_name = $LakehouseName
                }
            }
        }
        nbformat = 4
        nbformat_minor = 5
    }
    
    return $Notebook
}

# Function to upload notebook
function Upload-Notebook {
    param(
        [string]$WorkspaceId,
        [string]$NotebookName,
        [string]$NotebookJson,
        [string]$NotebookId = $null,
        [Hashtable]$Headers
    )
    
    # Encode to base64
    $JsonBytes = [System.Text.Encoding]::UTF8.GetBytes($NotebookJson)
    $B64 = [System.Convert]::ToBase64String($JsonBytes)
    
    $Payload = @{
        definition = @{
            format = "ipynb"
            parts = @(
                @{
                    path = "notebook-content.ipynb"
                    payloadType = "InlineBase64"
                    payload = $B64
                }
            )
        }
    } | ConvertTo-Json -Depth 10
    
    if ($NotebookId) {
        # Update existing
        $Url = "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/notebooks/$NotebookId/updateDefinition"
    } else {
        # Create new
        $Url = "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/items"
    }
    
    try {
        $Response = Invoke-RestMethod -Uri $Url -Method POST -Headers $Headers -Body $Payload
        return $true
    } catch {
        Write-Warning "Failed to upload $NotebookName : $($_.Exception.Message)"
        return $false
    }
}

# Process notebooks
$NotebooksToUpdate = @(
    @{ Name = "Utilities_init_session"; File = "Utilities_init_session.py" },
    @{ Name = "01_Ingestion_Setup_Bronze"; File = "01_Ingestion_Setup_Bronze.py" },
    @{ Name = "02_Transformation_Silver_Layer"; File = "02_Transformation_Silver_Layer.py" },
    @{ Name = "03_Dimensional_Model_Gold_Layer"; File = "03_Dimensional_Model_Gold_Layer.py" }
)

Write-Host "Reorganizing notebooks..." -ForegroundColor Cyan
Write-Host ""

foreach ($Notebook in $NotebooksToUpdate) {
    $FilePath = Join-Path "notebooks" $Notebook.File
    
    if (-not (Test-Path $FilePath)) {
        Write-Host "SKIP: $($Notebook.Name) - file not found" -ForegroundColor Gray
        continue
    }
    
    Write-Host "Processing $($Notebook.Name)..." -NoNewline
    
    # Read source
    $Source = Get-Content $FilePath -Raw -Encoding UTF8
    
    # Parse into cells
    $Cells = Parse-NotebookCells $Source
    Write-Host " ($($Cells.Count) cells)" -NoNewline
    
    # Create notebook
    $NotebookDict = Create-MultiCellNotebook $Cells $LakehouseId $WorkspaceId $LakehouseName
    $NotebookJson = $NotebookDict | ConvertTo-Json -Depth 10
    
    # Get existing notebook ID
    $ExistingItems = Invoke-RestMethod -Uri "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/items?type=Notebook" -Method GET -Headers $Headers
    $ExistingNotebook = $ExistingItems.value | Where-Object { $_.displayName -eq $Notebook.Name }
    
    # Upload
    if (Upload-Notebook $WorkspaceId $Notebook.Name $NotebookJson $ExistingNotebook.id $Headers) {
        Write-Host " [OK]" -ForegroundColor Green
    } else {
        Write-Host " [FAILED]" -ForegroundColor Red
    }
    
    Start-Sleep -Milliseconds 1500
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Reorganization Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "All notebooks have been updated with multiple cells."
Write-Host ""
Write-Host "Next step: Open notebooks in Fabric to see the organized cells!"
