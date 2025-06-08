"""
Directory Reorganization Script
Version: 1.0.0
Created: 2025-06-08 22:38:39
Author: anandhu723
"""

import os
import shutil
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_directory_structure():
    """Create the correct directory structure"""
    base_dirs = [
        'saveai/api/handlers',
        'saveai/core',
        'saveai/services',
        'saveai/tests/test_api',
        'saveai/deployment/docker/nginx/conf.d'
    ]
    
    for dir_path in base_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")

def move_files():
    """Move files to their correct locations"""
    file_mappings = {
        # API files
        'saveai/core/saveai/api/config.py': 'saveai/api/config.py',
        'saveai/core/saveai/api/middleware.py': 'saveai/api/middleware.py',
        'saveai/core/saveai/api/router.py': 'saveai/api/router.py',
        
        # Tests
        'saveai/core/saveai/tests/__init__.py': 'saveai/tests/__init__.py',
        'saveai/core/saveai/tests/conftest.py': 'saveai/tests/conftest.py',
        'saveai/core/saveai/tests/test_api/test_analytics.py': 'saveai/tests/test_api/test_analytics.py',
        'saveai/core/saveai/tests/test_api/test_blockchain.py': 'saveai/tests/test_api/test_blockchain.py',
        'saveai/core/saveai/tests/test_api/test_security.py': 'saveai/tests/test_api/test_security.py',
        'saveai/core/saveai/tests/test_api/test_tax.py': 'saveai/tests/test_api/test_tax.py',
        'saveai/core/saveai/tests/test_api/test_transaction.py': 'saveai/tests/test_api/test_transaction.py',
        
        # Deployment
        'saveai/core/saveai/deployment/docker/Dockerfile': 'saveai/deployment/docker/Dockerfile',
        'saveai/core/saveai/deployment/docker/docker-compose.yml': 'saveai/deployment/docker/docker-compose.yml',
        'saveai/core/saveai/deployment/docker/.env.example': 'saveai/deployment/docker/.env.example',
        'saveai/core/saveai/deployment/docker/nginx/conf.d/default.conf': 'saveai/deployment/docker/nginx/conf.d/default.conf'
    }
    
    for src, dst in file_mappings.items():
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            logger.info(f"Moved {src} to {dst}")
        else:
            logger.warning(f"Source file not found: {src}")

def cleanup_empty_dirs():
    """Remove empty directories"""
    for root, dirs, files in os.walk('saveai', topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                os.rmdir(dir_path)
                logger.info(f"Removed empty directory: {dir_path}")
            except OSError:
                pass  # Directory not empty

def main():
    """Main execution function"""
    logger.info("Starting directory restructuring...")
    
    # Create new structure
    setup_directory_structure()
    
    # Move files
    move_files()
    
    # Cleanup empty directories
    cleanup_empty_dirs()
    
    logger.info("Directory restructuring completed!")

if __name__ == "__main__":
    main()
