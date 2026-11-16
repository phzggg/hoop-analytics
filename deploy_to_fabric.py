#!/usr/bin/env python3
"""
NBA Live Data Platform - Fabric Deployment Script
Deploys historical Phase 3 notebooks and creates a lakehouse in a specified workspace.
"""

import subprocess
import argparse
import json
import sys
import time
import base64
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FabricDeployer:
    """Handles deployment of notebooks to Fabric workspace"""
    
    def __init__(self, workspace_name: str, lakehouse_name: str = "nba_lakehouse"):
        self.workspace_name = workspace_name
        self.lakehouse_name = lakehouse_name
        self.workspace_id = None
        self.lakehouse_id = None
        self.notebooks_dir = Path("notebooks")
        
    def run_command(self, cmd: list, capture_output: bool = True) -> Dict[str, Any]:
        """Execute az command and return result"""
        try:
            # If cmd starts with 'az', replace with full path
            if cmd[0] == "az":
                cmd[0] = r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
            
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                check=False,
                shell=True
            )
            if result.returncode != 0:
                logger.error(f"Command failed: {' '.join(cmd)}")
                logger.error(f"stderr: {result.stderr}")
                return {"success": False, "error": result.stderr}
            return {"success": True, "output": result.stdout}
        except Exception as e:
            logger.error(f"Exception running command: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_workspaces(self) -> Optional[Dict]:
        """Get all workspaces"""
        logger.info("Fetching workspaces...")
        cmd = [
            "az", "rest",
            "--method", "GET",
            "--url", "https://api.powerbi.com/v1.0/myorg/workspaces",
            "--headers", "x-ms-fabric-skill=spark-cli",
            "--output", "json"
        ]
        result = self.run_command(cmd)
        if not result["success"]:
            return None
        try:
            return json.loads(result["output"])
        except:
            logger.error("Failed to parse workspaces JSON")
            return None
    
    def find_workspace_id(self) -> bool:
        """Find workspace ID by name"""
        workspaces = self.get_workspaces()
        if not workspaces or "value" not in workspaces:
            logger.error(f"Could not find workspaces")
            return False
        
        for ws in workspaces.get("value", []):
            if ws.get("name") == self.workspace_name:
                self.workspace_id = ws.get("id")
                logger.info(f"Found workspace '{self.workspace_name}' with ID: {self.workspace_id}")
                return True
        
        logger.error(f"Workspace '{self.workspace_name}' not found")
        return False
    
    def list_items(self, workspace_id: str, item_type: str = "") -> Optional[Dict]:
        """List items in workspace"""
        url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items"
        if item_type:
            url += f"?type={item_type}"
        
        cmd = [
            "az", "rest",
            "--method", "GET",
            "--url", url,
            "--headers", "x-ms-fabric-skill=spark-cli",
            "--output", "json"
        ]
        result = self.run_command(cmd)
        if not result["success"]:
            return None
        try:
            return json.loads(result["output"])
        except:
            logger.error(f"Failed to parse items JSON for workspace {workspace_id}")
            return None
    
    def find_lakehouse_id(self) -> bool:
        """Find or create lakehouse"""
        items = self.list_items(self.workspace_id, "Lakehouse")
        if not items or "value" not in items:
            logger.warning(f"Could not fetch lakehouses")
            return self.create_lakehouse()
        
        for item in items.get("value", []):
            if item.get("displayName") == self.lakehouse_name:
                self.lakehouse_id = item.get("id")
                logger.info(f"Found lakehouse '{self.lakehouse_name}' with ID: {self.lakehouse_id}")
                return True
        
        logger.info(f"Lakehouse '{self.lakehouse_name}' not found, creating...")
        return self.create_lakehouse()
    
    def create_lakehouse(self) -> bool:
        """Create a new lakehouse"""
        logger.info(f"Creating lakehouse '{self.lakehouse_name}'...")
        
        payload = {
            "displayName": self.lakehouse_name,
            "type": "Lakehouse"
        }
        
        cmd = [
            "az", "rest",
            "--method", "POST",
            "--url", f"https://api.fabric.microsoft.com/v1/workspaces/{self.workspace_id}/items",
            "--headers", "x-ms-fabric-skill=spark-cli", "Content-Type=application/json",
            "--body", json.dumps(payload),
            "--output", "json"
        ]
        
        result = self.run_command(cmd)
        if not result["success"]:
            logger.error(f"Failed to create lakehouse: {result['error']}")
            return False
        
        try:
            response = json.loads(result["output"])
            self.lakehouse_id = response.get("id")
            logger.info(f"Lakehouse created with ID: {self.lakehouse_id}")
            return True
        except:
            logger.error("Failed to parse lakehouse creation response")
            return False
    
    def create_notebook(self, notebook_name: str, notebook_file: Path) -> bool:
        """Create or update a notebook"""
        if not notebook_file.exists():
            logger.error(f"Notebook file not found: {notebook_file}")
            return False
        
        logger.info(f"Deploying notebook: {notebook_name}")
        
        # Read notebook source
        with open(notebook_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # For Fabric, we need to create a .ipynb format notebook
        # Create basic ipynb structure
        notebook_dict = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [line + '\n' for line in source_code.split('\n')]
                }
            ],
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
                        "default_lakehouse": self.lakehouse_id,
                        "default_lakehouse_workspace_id": self.workspace_id,
                        "default_lakehouse_name": self.lakehouse_name
                    }
                }
            },
            "nbformat": 4,
            "nbformat_minor": 5
        }
        
        # Encode to base64
        notebook_json = json.dumps(notebook_dict, ensure_ascii=False)
        notebook_b64 = base64.b64encode(notebook_json.encode('utf-8')).decode('ascii')
        
        # Check if notebook exists
        items = self.list_items(self.workspace_id, "Notebook")
        notebook_id = None
        if items and "value" in items:
            for item in items.get("value", []):
                if item.get("displayName") == notebook_name:
                    notebook_id = item.get("id")
                    break
        
        if notebook_id:
            # Update existing notebook
            logger.info(f"Updating existing notebook: {notebook_name}")
            return self.update_notebook(notebook_id, notebook_name, notebook_b64)
        else:
            # Create new notebook
            logger.info(f"Creating new notebook: {notebook_name}")
            return self.create_new_notebook(notebook_name, notebook_b64)
    
    def create_new_notebook(self, notebook_name: str, notebook_b64: str) -> bool:
        """Create a new notebook item"""
        payload = {
            "displayName": notebook_name,
            "type": "Notebook",
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
        
        cmd = [
            "az", "rest",
            "--method", "POST",
            "--url", f"https://api.fabric.microsoft.com/v1/workspaces/{self.workspace_id}/items",
            "--headers", "x-ms-fabric-skill=spark-cli", "Content-Type=application/json",
            "--body", json.dumps(payload),
            "--output", "json"
        ]
        
        result = self.run_command(cmd)
        if not result["success"]:
            logger.error(f"Failed to create notebook '{notebook_name}': {result['error']}")
            return False
        
        logger.info(f"Notebook '{notebook_name}' created successfully")
        return True
    
    def update_notebook(self, notebook_id: str, notebook_name: str, notebook_b64: str) -> bool:
        """Update an existing notebook"""
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
        
        cmd = [
            "az", "rest",
            "--method", "POST",
            "--url", f"https://api.fabric.microsoft.com/v1/workspaces/{self.workspace_id}/notebooks/{notebook_id}/updateDefinition",
            "--headers", "x-ms-fabric-skill=spark-cli", "Content-Type=application/json",
            "--body", json.dumps(payload),
            "--output", "json"
        ]
        
        result = self.run_command(cmd)
        if not result["success"]:
            logger.error(f"Failed to update notebook '{notebook_name}': {result['error']}")
            return False
        
        logger.info(f"Notebook '{notebook_name}' updated successfully")
        return True
    
    def deploy_all(self) -> bool:
        """Deploy all notebooks"""
        logger.info("=" * 60)
        logger.info("NBA Live Data Platform - Fabric Deployment")
        logger.info("=" * 60)
        
        # Step 1: Find workspace
        if not self.find_workspace_id():
            logger.error("Deployment failed: workspace not found")
            return False
        
        # Step 2: Find or create lakehouse
        if not self.find_lakehouse_id():
            logger.error("Deployment failed: could not create lakehouse")
            return False
        
        # Step 3: Deploy notebooks in order
        notebooks_to_deploy = [
            ("Utilities_init_session", self.notebooks_dir / "Utilities_init_session.py"),
            ("01_Ingestion_Setup_Bronze", self.notebooks_dir / "01_Ingestion_Setup_Bronze.py"),
            ("02_Transformation_Silver_Layer", self.notebooks_dir / "02_Transformation_Silver_Layer.py"),
            ("03_Dimensional_Model_Gold_Layer", self.notebooks_dir / "03_Dimensional_Model_Gold_Layer.py"),
        ]
        
        success_count = 0
        for notebook_name, notebook_file in notebooks_to_deploy:
            if self.create_notebook(notebook_name, notebook_file):
                success_count += 1
            time.sleep(2)  # Rate limiting
        
        logger.info("=" * 60)
        logger.info(f"Deployment Complete: {success_count}/{len(notebooks_to_deploy)} notebooks deployed")
        logger.info("=" * 60)
        logger.info("\nNext Steps:")
        logger.info("1. Go to workspace '%s' in Fabric", self.workspace_name)
        logger.info("2. Run notebooks in order:")
        logger.info("   - Utilities_init_session (setup)")
        logger.info("   - 01_Ingestion_Setup_Bronze (5-10 min)")
        logger.info("   - 02_Transformation_Silver_Layer (5-10 min)")
        logger.info("   - 03_Dimensional_Model_Gold_Layer (3-5 min)")
        
        return success_count == len(notebooks_to_deploy)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, help="Fabric workspace name")
    args = parser.parse_args()
    deployer = FabricDeployer(workspace_name=args.workspace)
    success = deployer.deploy_all()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
