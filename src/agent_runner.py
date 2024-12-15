"""
===================================================================================================
Title : agent_runner.py

Description : responsible for running tasks, and spawning workers

Copyright 2024 - Jadkins-Me

This Code/Software is licensed to you under GNU AFFERO GENERAL PUBLIC LICENSE (GPL), Version 3
Unless required by applicable law or agreed to in writing, the Code/Software distributed
under the GPL Licence is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. Please review the Licences for the specific language governing
permissions and limitations relating to use of the Code/Software.

===================================================================================================
"""
import constants
import inspect
import logging
from log import LogWriter
from tasks import Agent_Task
import threading 
import time 
from datetime import datetime, timedelta
from agent_download import AgentDownloader

#get a handle to the logging class
log_writer = LogWriter()

#to-do: these should not be here
CONST_DEFAULT_WORKERS = 1
CONST_MAX_WORKERS = 10

CONST_DEFAULT_FILESIZE = "tiny"
CONST_FILESIZES = { "small": "small", "tiny": "tiny", "huge": "huge" } 

CONST_DEFAULT_OFFSET = 0
CONST_DEFAULT_RETRY = 3
CONST_DEFAULT_TIMEOUT = 30
CONST_DEFAULT_REPEAT = False

#This can go multi-class, be aware of thread safety !
class AgentRunner:
    def __init__(self):
        self.__AgentRunnerRef = ""
        self.downloadclients = [] 
        self.created_time = datetime.now()
        log_writer.log(f"> > {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: created={self.created_time.strftime('%Y-%m-%d %H:%M:%S')}", logging.INFO )

        # Calculate the time until the next 55-minute mark 
        self.schedule_self_destruct()

    def exec_upload_task(self, task):
        pass

    def exec_quote_task(self, task):
        pass
    
    def exec_download_task(self, task):
        log_writer.log(f"> > {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: INVOKE",logging.INFO)

        self.__AgentRunnerRef = task.task_ref  # Make sure this is being set correctly

        # Get the workers value and ensure it's an integer, defaulting to the integer default if not present 
        workers = min(int(task.test_options.get('workers', CONST_DEFAULT_WORKERS)), CONST_MAX_WORKERS)
        
        filesize = task.test_options.get('filesize', CONST_DEFAULT_FILESIZE)
        if filesize.lower() in CONST_FILESIZES:
            filesize = CONST_FILESIZES[filesize.lower()]
        else:
            filesize = CONST_DEFAULT_FILESIZE
        
        offset = task.test_options.get('offset', CONST_DEFAULT_OFFSET)
        timeout = task.test_options.get('timeout', CONST_DEFAULT_TIMEOUT)
        retry = task.test_options.get('retry', CONST_DEFAULT_RETRY)
        repeat = task.test_options.get('repeat', CONST_DEFAULT_REPEAT)
        
        log_writer.log(f"> > {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: task_ref:{task.task_ref}, filesize:{filesize}, workers:{workers}",logging.INFO)
        
        threads = []

        #spawn the thread workers
        for i in range(workers):
            downloadclient = AgentDownloader()
            self.downloadclients.append(downloadclient)
            thread = threading.Thread(target=downloadclient.download, args=(filesize, offset, timeout, retry, repeat), name=f"Thread-2(AgentRunner.exec_download_task).{task.task_ref}.{self.created_time.strftime('%Y-%m-%d %H:%M:%S')}")
            threads.append(thread)
            thread.start()
        
        # Calculate time left until the 55th minute of the current hour 
        now = datetime.now()
        seconds_to_55 = ((55 - now.minute) * 60) - now.second
        
        # Wait for threads to complete or time out 
        start_time = time.time()
        for thread in threads:
            elapsed = time.time() - start_time
            remaining_time = seconds_to_55 - elapsed
            if remaining_time > 0:
                while thread.is_alive() and remaining_time > 0:
                    thread.join(timeout=1)  # Check every second
                    remaining_time -= 1
                #endWhile
            #endIf
            if thread.is_alive():
                log_writer.log(f"Terminating thread {thread.name} as it exceeded time limit", logging.WARNING)
                # Threads cannot be forcefully terminated in Python :( #sad, so we log and move on
            #endIf
        #endFor
        log_writer.log(f"< < {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: return: NONE",logging.INFO)

        #make sure we try and hand the thread back :to-do need better thread safety code, as if this is missed we can run out of threads !
        self.cleanup()
        
    def schedule_self_destruct(self): #todo: tidy this up
        now = datetime.now() 
        minutes = now.minute 
        seconds = now.second 
        if minutes < 55: 
            minutes_to_wait = 55 - minutes 
        else: 
            minutes_to_wait = (60 - minutes) + 55 # to the next hour and 55 minutes 
        
        seconds_to_wait = minutes_to_wait * 60 - seconds 
        log_writer.log(f"- - {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: class self-destruction in {seconds_to_wait} seconds", logging.INFO )

        self.deletion_thread = threading.Timer(seconds_to_wait, self.self_destruct) 
        self.deletion_thread.start() 
    
    def self_destruct(self): 
        log_writer.log(f"> > {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: self-destructed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", logging.INFO)
        self.cleanup() # Ensure cleanup is called 
    
    def cleanup(self): 
        # Perform cleanup operations here
        if self.deletion_thread.is_alive(): 
            self.deletion_thread.cancel()
        else: 
            self.deletion_thread.join(timeout=5)

        log_writer.log(f"AgentRunner instance cleaned up at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", logging.INFO) 

        for runner in self.downloadclients: 
            runner.cleanup() 
        #endFor

        log_writer.log(f"< < {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: Instance Deleted", logging.INFO)
        del self