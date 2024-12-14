"""
===============================================================================
Title : version.py

Description : Version information that will be returned including GIT Hash

===============================================================================
"""

import subprocess

def get_git_commit_hash():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).strip().decode('utf-8')
    except Exception:
        return "Unknown"

BUILD_VERSION = "0.1.1"
BUILD_DATE = "14-12-2024"
BUILD_NAME = "ant-agent"

COMMIT_HASH = get_git_commit_hash()