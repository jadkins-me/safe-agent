"""
===================================================================================================
Title : agent_limiter.py

Description : global limiter to manager total agent load

Copyright 2024 - Jadkins-Me

This Code/Software is licensed to you under GNU AFFERO GENERAL PUBLIC LICENSE (GPL), Version 3
Unless required by applicable law or agreed to in writing, the Code/Software distributed
under the GPL Licence is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. Please review the Licences for the specific language governing
permissions and limitations relating to use of the Code/Software.

===================================================================================================
"""
from ratelimit import limits, RateLimitException 
from log import LogWriter 
import logging 
from datetime import datetime, timedelta

#handle to log processing
log_writer = LogWriter()

# Define the rate limit (60 requests per hour) 
CONST_ONE_HOUR = 3600 

# Define the cooldown period for handling RateLimitException (5 minutes) 
CONST_FIVE_MINUTES = timedelta(minutes=5) 

# Timestamp to track the last time the rate limit exception was handled 
last_exception_time = datetime.min

#to-do - BROKEN, need to sort out the scope and debug
def download_rate_limit(func): 
    def wrapper(*args, **kwargs): 
        global last_exception_time 
        try: 
            return func(*args, **kwargs) 
        except RateLimitException: 
            current_time = datetime.now() 
            if current_time - last_exception_time >= CONST_FIVE_MINUTES: 
                last_exception_time = current_time 
                log_writer.log(f"!!!rate limit applied - too many download requests, suppressing for 5 minutes", logging.INFO) 
            return None 
    return wrapper

# Notes : This is a single instance class, so ensure that is enforced.
class Limiter:
    #Ensure this is a single instance class
    _instance = None

    def __new__(cls, *args, **kwargs): 
        if not cls._instance: cls._instance = super(Limiter, cls).__new__(cls, *args, **kwargs) 
        return cls._instance 
    
    def __init__(self): 
        if not hasattr(self, 'initialized'): 
            # Ensure __init__ runs only once 
            self.initialized = True 
    
    @download_rate_limit 
    @limits(calls=2, period=CONST_ONE_HOUR) # Adjusted to 2 requests per hour 
    def __download_limiter(self): 
        return True , None

    def push_download(self) -> bool: 
        try: 
            result = self.__download_limiter() 
            if result: 
                return True 
            else: 
                return False 
        except RateLimitException: 
            return True # Return True when limit is reached

    def push_upload(self) -> bool:
        return False

    def push_quote(self) -> bool:
        return False
    
    def show_limits(self):
        #to:do
        log_writer.log(f"Rate Limiting Active : Download (2 calls/hour) / Upload (undefined) / Quote (undefined)",logging.INFO)
        