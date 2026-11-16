# NBA Live Data Platform - Fabric Deployment Script

param(
    [Parameter(Mandatory = $true)][string]$WorkspaceName,
    [string]$LakehouseName = "nba_lakehouse"
)

$ErrorActionPreference = "Stop"

# Get access token
Write-Host "Authenticating..." -ForegroundColor Yellow
$TokenResponse = az account get-access-token --resource "https://api.fabric.microsoft.com" | ConvertFrom-Json
$Token = $TokenResponse.accessToken

# Helper function to call Fabric API
function Invoke-FabricAPI {
    param(
        [string]$Method,
        [string]$Endpoint,
        $Body = $null,
        [string]$Token
    )
    
    $Url = "https://api.fabric.microsoft.com$Endpoint"
    $Headers = @{
        "Authorization" = "Bearer $Token"
        "x-ms-fabric-skill" = "spark-cli"
        "Content-Type" = "application/json"
    }
    
    $Params = @{
        Uri = $Url
        Method = $Method
        Headers = $Headers
    }
    
    if ($Body) {
        $Params["Body"] = ($Body | ConvertTo-Json -Depth 10)
    }
    
    try {
        $Response = Invoke-RestMethod @Params
        return $Response
    } catch {
        Write-Warning "API Error: $($_.Exception.Message)"
        return $null
    }
}

Write-Host "NBA Live Data Platform - Fabric Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Get workspace
Write-Host "Step 1: Finding workspace..." -ForegroundColor Yellow
$Workspaces = Invoke-FabricAPI -Method GET -Endpoint "/v1/workspaces" -Token $Token
$Workspace = $Workspaces.value | Where-Object { $_.displayName -eq $WorkspaceName }

if (-not $Workspace) {
    Write-Host "ERROR: Workspace '$WorkspaceName' not found" -ForegroundColor Red
    exit 1
}

$WorkspaceId = $Workspace.id
Write-Host "Found workspace: $WorkspaceName" -ForegroundColor Green
Write-Host ""

# Step 2: Find or create lakehouse
Write-Host "Step 2: Checking lakehouse..." -ForegroundColor Yellow
$Items = Invoke-FabricAPI -Method GET -Endpoint "/v1/workspaces/$WorkspaceId/items?type=Lakehouse" -Token $Token
$Lakehouse = $Items.value | Where-Object { $_.displayName -eq $LakehouseName }

if ($Lakehouse) {
    $LakehouseId = $Lakehouse.id
    Write-Host "Found lakehouse: $LakehouseName" -ForegroundColor Green
} else {
    Write-Host "Creating lakehouse: $LakehouseName..." -NoNewline
    $LakehousePayload = @{
        displayName = $LakehouseName
        type = "Lakehouse"
    }
    $NewLakehouse = Invoke-FabricAPI -Method POST -Endpoint "/v1/workspaces/$WorkspaceId/items" -Body $LakehousePayload -Token $Token
    $LakehouseId = $NewLakehouse.id
    Write-Host " Done" -ForegroundColor Green
}
Write-Host ""

# Step 3: Deploy notebooks
Write-Host "Step 3: Deploying notebooks..." -ForegroundColor Yellow
Write-Host ""

$Notebooks = @(
    @{ Name = "Utilities_init_session"; File = "Utilities_init_session.py" },
    @{ Name = "01_Ingestion_Setup_Bronze"; File = "01_Ingestion_Setup_Bronze.py" },
    @{ Name = "02_Transformation_Silver_Layer"; File = "02_Transformation_Silver_Layer.py" },
    @{ Name = "03_Dimensional_Model_Gold_Layer"; File = "03_Dimensional_Model_Gold_Layer.py" }
)

$DeployedCount = 0

foreach ($Notebook in $Notebooks) {
    $FilePath = Join-Path "notebooks" $Notebook.File
    
    if (-not (Test-Path $FilePath)) {
        Write-Host "SKIP: $($Notebook.Name) - file not found" -ForegroundColor Gray
        continue
    }
    
    Write-Host "  Deploying $($Notebook.Name)..." -NoNewline
    
    # Read and encode source
    $Source = Get-Content $FilePath -Raw -Encoding UTF8
    $SourceLines = @($Source -split "`n" | ForEach-Object { $_ + "`n" }) | Select-Object -SkipLast 1
    
    # Create notebook structure
    $NotebookData = @{
        cells = @(
            @{
                cell_type = "code"
                execution_count = $null
                metadata = @{}
                outputs = @()
                source = $SourceLines
            }
        )
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
    
    # Encode to base64
    $Json = $NotebookData | ConvertTo-Json -Depth 10
    $Bytes = [System.Text.Encoding]::UTF8.GetBytes($Json)
    $B64 = [System.Convert]::ToBase64String($Bytes)
    
    # Check if exists
    $ExistingItems = Invoke-FabricAPI -Method GET -Endpoint "/v1/workspaces/$WorkspaceId/items?type=Notebook" -Token $Token
    $ExistingNotebook = $ExistingItems.value | Where-Object { $_.displayName -eq $Notebook.Name }
    
    if ($ExistingNotebook) {
        # Update
        $UpdateBody = @{
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
        }
        $Result = Invoke-FabricAPI -Method POST `
            -Endpoint "/v1/workspaces/$WorkspaceId/notebooks/$($ExistingNotebook.id)/updateDefinition" `
            -Body $UpdateBody -Token $Token
    } else {
        # Create
        $CreateBody = @{
            displayName = $Notebook.Name
            type = "Notebook"
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
        }
        $Result = Invoke-FabricAPI -Method POST `
            -Endpoint "/v1/workspaces/$WorkspaceId/items" `
            -Body $CreateBody -Token $Token
    }
    
    if ($Result) {
        Write-Host " OK" -ForegroundColor Green
        $DeployedCount++
    } else {
        Write-Host " FAILED" -ForegroundColor Red
    }
    
    Start-Sleep -Milliseconds 1000
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT COMPLETE" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Workspace: $WorkspaceName" -ForegroundColor White
Write-Host "Lakehouse: $LakehouseName" -ForegroundColor White
Write-Host "Notebooks: $DeployedCount deployed" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Open Fabric workspace: $WorkspaceName" -ForegroundColor White
Write-Host "2. Run notebooks in order:" -ForegroundColor White
Write-Host "   - Utilities_init_session" -ForegroundColor White
Write-Host "   - 01_Ingestion_Setup_Bronze" -ForegroundColor White
Write-Host "   - 02_Transformation_Silver_Layer" -ForegroundColor White
Write-Host "   - 03_Dimensional_Model_Gold_Layer" -ForegroundColor White
