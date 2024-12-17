"""
===================================================================================================
Title : application.py

Description : Instance of the agent, with all application specific classes

Copyright 2024 - Jadkins-Me

This Code/Software is licensed to you under GNU AFFERO GENERAL PUBLIC LICENSE (GPL), Version 3
Unless required by applicable law or agreed to in writing, the Code/Software distributed
under the GPL Licence is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. Please review the Licences for the specific language governing
permissions and limitations relating to use of the Code/Software.

===================================================================================================
"""

class Agent:
    #Ensure this is a single instance class
    _instance = None

    #Thread Control Signals
    __bool_agent_shutdown = False               # Set to True when agent is being shutdown
    __bool_threads_terminate = False    
    __bool_threads_scheduler_terminate = False
    __bool_threads_scheduler_paused = False

    __int_thread_task_count = 0
    __int_thread_worker_count = 0
    
    import version              # Version Information on Agent

    Exception = None            # Application Exception Handler class
    Configuration = None        # Application Configuration
   
# +++ Start: Single Instance class init
    def __new__(cls, *args, **kwargs): 
        if not cls._instance: cls._instance = super(Agent, cls).__new__(cls, *args, **kwargs) 
        return cls._instance 
    
    def __init__(self): 
        if not hasattr(self, 'initialized'): 
            # Ensure __init__ runs only once 
            self.initialized = True

    def start(self):       #must be called once to initilize the instances, but can't be called in __init__ as circular
        if not hasattr(self, 'started'):
            # Esure start runs only once
            
            if not self.Exception:
                self.Exception = _Agent__ExceptionHandler()

            if not self.Configuration:
                self.Configuration = _Agent__Configuration()
# +++ Definitions

    #Thread Task
    def push_thread_task(self):
        self.__int_thread_task_count+=1
    def pop_thread_task(self):
        self.__int_thread_task_count-=1
    def get_thread_task(self) -> int:
        return self.__int_thread_task_count
    
    #Thread Worker
    def push_thread_worker(self):
        self.__int_thread_worker_count+=1
    def pop_thread_worker(self):
        self.__int_thread_worker_count-=1
    def get_thread_worker(self) -> int:
        return self.__int_thread_worker_count


    def is_Threads_Terminate_Requested(self) -> bool:
        return self.__bool_threads_terminate
    def exec_Threads_Terminate(self):
            self.__bool_threads_terminate = True

    def is_Scheduler_Terminate_Requested(self) -> bool:
        return self.__bool_threads_scheduler_terminate
    def exec_Scheduler_Terminate(self):
            self.__bool_threads_scheduler_terminate = True

    def is_Scheduler_Paused(self) -> bool:
        return self.__bool_threads_scheduler_paused
    def start_Scheduler(self):
        self.__bool_threads_scheduler_paused = False
    def pause_Scheduler(self):
        self.__bool_threads_scheduler_paused = True
    
    def __set_agent_shutdown(self):
        self.__bool_agent_shutdown = True
    def is_Agent_Shutdown(self) -> bool :
        return(self.__bool_agent_shutdown)
    def exec_Shutdown(self):
        self.__set_agent_shutdown()
        #will need a handler to give threads time
        


# Global handler to allow threads a method of calling back to the main.py routine, to flag they have
# experienced an exception - Fatal, that should cause the program to terminate.
#
# Notes : This is a single instance class, so ensure that is enforced.
class _Agent__ExceptionHandler:
    #Ensure this is a single instance class
    _instance = None

    _class_exception = False
    _class_exception_err = None
    
    def __new__(cls, *args, **kwargs): 
        if not cls._instance: cls._instance = super(_Agent__ExceptionHandler, cls).__new__(cls, *args, **kwargs) 
        return cls._instance 
    
    def __init__(self): 
        if not hasattr(self, 'initialized'): 
            # Ensure __init__ runs only once 
            self.initialized = True 

    # Check if a program exception has been raised
    def has_occurred(self):
        if self._class_exception:
            return True
        else:
            return False
        #endIf

    def get(self):
        return (self._class_exception_err)
    
    # can use following shorthand, to extract calling class, by importing inspect module
    # {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}
    def throw(self, error=None):
        self._class_exception_err = ""
        if error is not None: 
            if isinstance(error, str): 
                self._class_exception_err = error 
            #endIf
        #endIf
        self._class_exception=True


# Notes : This is a single instance class, so ensure that is enforced.
class _Agent__Configuration:
    #Ensure this is a single instance class
    _instance = None

    # European date format
    DATE_FORMAT = '%d-%m-%Y %H:%M:%S'

    # Logging constants
    LOG_FILE_PATH = './agent-ant.log'
    LOG_TO_FILE = False
    DEFAULT_LOG_LEVEL = 'INFO'  # DEBUG, ERROR, WARN, INFO #to-do : needs changing else too verbose

    SCHEDULER_CHECK = ":00" # What time (minutes) the scheduler will check for new jobs
    SCHEDULER_URL = 'https://raw.githubusercontent.com/jadkins-me/safe-agent/main/tests/00-control.xml'
    SCHEDULER_NO_TASKS = [56, 57, 58, 59, 0, 1, 2, 3, 4]   # minutes when the schedule can't start new tasks

    GIT_OWNER = "jadkins-me"
    GIT_REPO = "safe-agent"
    GIT_KILL_SWITCH_URL = "https://api.github.com/repos/{owner}/{repo}/issues"

    CACHE_FILE = './cache/cached_files.csv' 
    CACHE_INFO_FILE = './cache/cache_info.json' 
    CACHE_TIME = 3600 # 1 hour in seconds (must be only seconds)
    CSV_URL = 'https://raw.githubusercontent.com/jadkins-me/safe-agent/main/tests/01-download-files.csv' 

    DOWNLOAD_YIELD_SECS = 10 # When in repeat mode, this is how many seconds we yield on a thread before repeating
    DOWNLOAD_OFFSET_MAX_MINS = 10 # Maximum minutes allows for offsetting tasks
    
    def __new__(cls, *args, **kwargs): 
        if not cls._instance: cls._instance = super(_Agent__Configuration, cls).__new__(cls, *args, **kwargs) 
        return cls._instance 
    
    def __init__(self): 
        if not hasattr(self, 'initialized'): 
            # Ensure __init__ runs only once 
            self.initialized = True 

    def load (self):
        #todo - load settings from env, config file, and pass any args
        global DEFAULT_LOG_LEVEL
        global LOG_TO_FILE
        DEFAULT_LOG_LEVEL = 'DEBUG'
        LOG_TO_FILE = True