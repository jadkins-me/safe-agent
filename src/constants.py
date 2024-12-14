"""
===============================================================================
Title : constants.py

Description : Settings for the program, don't change unless you know what you
are doing !

===============================================================================
"""

# European date format
DATE_FORMAT = '%d-%m-%Y %H:%M:%S'

# Logging constants
LOG_FILE_PATH = './agent-ant.log'
DEFAULT_LOG_LEVEL = 'INFO'

SCHEDULER_CHECK = ":00"
SCHEDULER_URL = 'https://raw.githubusercontent.com/jadkins-me/safe-agent/main/tests/00-control.xml'

GIT_OWNER = "jadkins-me"
GIT_REPO = "safe-agent"
GIT_KILL_SWITCH_URL = "https://api.github.com/repos/{owner}/{repo}/issues"

CACHE_FILE = './cache/cached_files.csv' 
CACHE_INFO_FILE = './cache/cache_info.json' 
CACHE_TIME = 3600 # 1 hour in seconds 
CSV_URL = 'https://raw.githubusercontent.com/jadkins-me/safe-agent/main/tests/01-download-files.csv' 