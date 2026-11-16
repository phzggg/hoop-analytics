#!/usr/bin/env python3
"""
Reorganize notebooks into multiple cells by splitting on cell markers
and upload updated versions to Fabric
"""

import json
import base64
import argparse
import subprocess
from pathlib import Path
from typing import List, Tuple

def parse_notebook_into_cells(source_code: str) -> List[str]:
    """
    Parse Python source code into cells based on cell markers
    Cell markers: # Cell N: ... or # ============
    """
    lines = source_code.split('\n')
    cells = []
    current_cell = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this line starts a new cell (Cell N: pattern)
        if line.strip().startswith('# Cell ') and ':' in line:
            # Save previous cell if it has content
            cell_content = '\n'.join(current_cell).strip()
            if cell_content and cell_content != '# ============================================':
                cells.append(cell_content)
            current_cell = []
            
            # Skip the separator line if it exists
            if i + 1 < len(lines) and lines[i + 1].strip().startswith('# ==='):
                i += 2
                continue
            else:
                i += 1
                continue
        
        current_cell.append(line)
        i += 1
    
    # Add final cell
    cell_content = '\n'.join(current_cell).strip()
    if cell_content:
        cells.append(cell_content)
    
    # Filter out empty cells
    cells = [c for c in cells if c.strip() and c.strip() != '# ============================================']
    
    return cells

def create_ipynb_with_multiple_cells(cells: List[str], lakehouse_id: str, workspace_id: str, lakehouse_name: str) -> dict:
    """
    Create a .ipynb notebook structure with multiple cells
    """
    notebook_cells = []
    
    for i, cell_source in enumerate(cells):
        # Ensure source lines end with \n except the last one
        source_lines = cell_source.split('\n')
        formatted_source = [line + '\n' for line in source_lines[:-1]]
        if source_lines[-1]:  # Add last line without \n
            formatted_source.append(source_lines[-1])
        
        notebook_cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": formatted_source
        })
    
    notebook = {
        "cells": notebook_cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.11"
            },
            "dependencies": {
                "lakehouse": {
                    "default_lakehouse": lakehouse_id,
                    "default_lakehouse_workspace_id": workspace_id,
                    "default_lakehouse_name": lakehouse_name
                }
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }
    
    return notebook

def upload_notebook_to_fabric(workspace_id: str, notebook_name: str, notebook_json: str, notebook_id: str = None) -> bool:
    """Upload or update notebook in Fabric"""
    
    # Get token
    token_result = subprocess.run(
        ['az', 'account', 'get-access-token', '--resource', 'https://api.fabric.microsoft.com'],
        capture_output=True,
        text=True
    )
    
    if token_result.returncode != 0:
        print(f"Failed to get token: {token_result.stderr}")
        return False
    
    token = json.loads(token_result.stdout)['accessToken']
    
    # Encode notebook to base64
    notebook_bytes = notebook_json.encode('utf-8')
    notebook_b64 = base64.b64encode(notebook_bytes).decode('ascii')
    
    headers = {
        'Authorization': f'Bearer {token}',
        'x-ms-fabric-skill': 'spark-cli',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "definition": {
            "format": "ipynb",
            "parts": [
                {
                    "path": "notebook-content.ipynb",
                    "payloadType": "InlineBase64",
                    "payload": notebook_b64
                }
            ]
        }
    }
    
    if notebook_id:
        # Update existing
        url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/notebooks/{notebook_id}/updateDefinition"
    else:
        # Create new
        payload["displayName"] = notebook_name
        payload["type"] = "Notebook"
        url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items"
    
    result = subprocess.run(
        ['curl', '-X', 'POST', url, '-H', f'Authorization: Bearer {token}',
         '-H', 'x-ms-fabric-skill: spark-cli', '-H', 'Content-Type: application/json',
         '-d', json.dumps(payload)],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✓ {notebook_name} uploaded successfully")
        return True
    else:
        print(f"✗ Failed to upload {notebook_name}")
        print(f"  Error: {result.stderr}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Reorganize historical notebooks in a Fabric workspace")
    parser.add_argument("--workspace-id", required=True, help="Fabric workspace ID")
    args = parser.parse_args()
    notebooks_dir = Path('notebooks')
    notebooks_to_update = [
        'Utilities_init_session.py',
        '01_Ingestion_Setup_Bronze.py',
        '02_Transformation_Silver_Layer.py',
        '03_Dimensional_Model_Gold_Layer.py'
    ]
    
    # Workspace and lakehouse info
    workspace_id = args.workspace_id
    lakehouse_id = None  # Will fetch
    lakehouse_name = "nba_lakehouse"
    
    # First, get lakehouse ID
    print("Fetching lakehouse ID...")
    token_result = subprocess.run(
        ['az', 'account', 'get-access-token', '--resource', 'https://api.fabric.microsoft.com'],
        capture_output=True,
        text=True
    )
    token = json.loads(token_result.stdout)['accessToken']
    
    items_result = subprocess.run(
        ['curl', '-X', 'GET',
         f'https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items?type=Lakehouse',
         '-H', f'Authorization: Bearer {token}',
         '-H', 'x-ms-fabric-skill: spark-cli'],
        capture_output=True,
        text=True
    )
    
    try:
        items = json.loads(items_result.stdout)
        for item in items.get('value', []):
            if item.get('displayName') == lakehouse_name:
                lakehouse_id = item.get('id')
                break
    except:
        pass
    
    if not lakehouse_id:
        print("ERROR: Could not find lakehouse ID")
        return 1
    
    print(f"Lakehouse ID: {lakehouse_id}")
    print("")
    
    # Process each notebook
    for notebook_file in notebooks_to_update:
        notebook_path = notebooks_dir / notebook_file
        
        if not notebook_path.exists():
            print(f"SKIP: {notebook_file} - file not found")
            continue
        
        print(f"Processing: {notebook_file}")
        
        # Read source code
        with open(notebook_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # Parse into cells
        cells = parse_notebook_into_cells(source_code)
        print(f"  Parsed into {len(cells)} cells")
        
        # Create notebook structure
        notebook_dict = create_ipynb_with_multiple_cells(cells, lakehouse_id, workspace_id, lakehouse_name)
        notebook_json = json.dumps(notebook_dict, ensure_ascii=False)
        
        # Get notebook display name
        if notebook_file == 'Utilities_init_session.py':
            notebook_name = 'Utilities_init_session'
        else:
            notebook_name = notebook_file.replace('.py', '')
        
        # Get existing notebook ID (for update)
        notebook_id = None
        items_result = subprocess.run(
            ['curl', '-X', 'GET',
             f'https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items?type=Notebook',
             '-H', f'Authorization: Bearer {token}',
             '-H', 'x-ms-fabric-skill: spark-cli'],
            capture_output=True,
            text=True
        )
        
        try:
            items = json.loads(items_result.stdout)
            for item in items.get('value', []):
                if item.get('displayName') == notebook_name:
                    notebook_id = item.get('id')
                    break
        except:
            pass
        
        # Upload
        if upload_notebook_to_fabric(workspace_id, notebook_name, notebook_json, notebook_id):
            print(f"  ✓ Updated to {len(cells)} cells")
        else:
            print(f"  ✗ Failed to upload")
        
        print("")
    
    print("=" * 60)
    print("Notebook reorganization complete!")
    print("=" * 60)
    return 0

if __name__ == '__main__':
    exit(main())
