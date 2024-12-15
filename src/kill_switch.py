"""
===================================================================================================
Title : kill_switch.py

Copyright 2024 - Jadkins-Me

This Code/Software is licensed to you under GNU AFFERO GENERAL PUBLIC LICENSE (GPL), Version 3
Unless required by applicable law or agreed to in writing, the Code/Software distributed
under the GPL Licence is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. Please review the Licences for the specific language governing
permissions and limitations relating to use of the Code/Software.

===================================================================================================
"""

import requests
import constants
from datetime import datetime, timedelta
from log import LogWriter
from ratelimit import limits, RateLimitException 

#to-do : constants need moving

log_writer = LogWriter()

# Define the rate limit (60 requests per hour) 
CONST_ONE_HOUR = 3600 

# Define the cooldown period for handling RateLimitException (5 minutes) 
CONST_FIVE_MINUTES = timedelta(minutes=5) 

# Timestamp to track the last time the rate limit exception was handled 
last_exception_time = datetime.min

def ignore_rate_limit(func): 
    def wrapper(*args, **kwargs): 
        global last_exception_time 
        try: 
            return func(*args, **kwargs) 
        except RateLimitException: 
            current_time = datetime.now() 
            if current_time - last_exception_time >= CONST_FIVE_MINUTES: 
                last_exception_time = current_time 
                log_writer.log(f"Rate limit : check_for_kill_switch reached. Ignoring this request.") 
            else: 
                log_writer.logf("Rate limit spam being surpressed for 5 minutes.")
            #endIf    
            return None
        #endTry
    return wrapper

class GitHubRepoIssuesChecker:
    def __init__(self):
        self.owner = constants.GIT_OWNER
        self.repo = constants.GIT_REPO
        self.url = constants.GIT_KILL_SWITCH_URL

    def __get_issues(self):
        # Substitute the variables into the URL
        url = self.url.format(owner=self.owner, repo=self.repo)
        response = requests.get(url)
        response.raise_for_status()  # Raise an error if the request was unsuccessful
        return response.json()

    @ignore_rate_limit 
    @limits(calls=60, period=CONST_ONE_HOUR)
    def check_for_kill_switch(self):
        issues = self.__get_issues()
        for issue in issues:
            if issue['state'] == 'open':
                labels = [label['name'].lower() for label in issue['labels']]
                if 'kill-switch' in labels:
                    creation_date = issue['created_at']
                    # Parse the creation date and convert to European format with UTC time
                    creation_date = datetime.strptime(creation_date, "%Y-%m-%dT%H:%M:%SZ")
                    formatted_date = creation_date.strftime("%d/%m/%Y %H:%M:%S UTC")
                    return True, formatted_date
                #endIf
            #endIf
        #endFor
        return False, None
