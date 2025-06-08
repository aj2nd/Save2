"""
Directory Structure Verification Script
Version: 1.0.0
Created: 2025-06-08 23:07:57
Author: anandhu723
"""

import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_structure():
    expected_structure = {
        'saveai': {
            'api': ['config.py', 'middleware.py', 'router.py', 'handlers'],
            'core': [],
            'services': [],
            'tests': ['__init__.py', 'conftest.py', 'test_api'],
            'tests/test_api': [
                'test_analytics.py',
                'test_blockchain.py',
                'test_security.py',
                'test_tax.py'
            ],
            'deployment/docker': [
                'Dockerfile',
                'docker-compose.yml',
                '.env.example'
            ],
            'deployment/docker/nginx/conf.d': ['default.conf']
        }
    }
    
    def check_path(base_path, structure):
        for key, value in structure.items():
            path = Path(base_path) / key
            if not path.exists():
                logger.error(f"Missing directory: {path}")
                continue
            if isinstance(value, list):
                for file in value:
                    file_path = path / file
                    if not file_path.exists():
                        logger.error(f"Missing file: {file_path}")
                    else:
                        logger.info(f"Verified: {file_path}")
            else:
                check_path(path, value)

    logger.info("Starting structure verification...")
    check_path('.', expected_structure)
    logger.info("Structure verification completed!")

if __name__ == "__main__":
    verify_structure()
