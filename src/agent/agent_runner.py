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
from application import Agent
import inspect
import logging
from log import LogWriter
from tasks import Agent_Task
import threading 
import time 
from datetime import datetime, timedelta
from agent.agent_download import AgentDownloader

#get a handle to the logging class
log_writer = LogWriter()
cls_agent = Agent()

#to-do: these should not be here
CONST_DEFAULT_WORKERS = 1
CONST_MAX_WORKERS = 10

CONST_DEFAULT_FILESIZE = "tiny"
CONST_FILESIZES = { 
    "tiny": "tiny", 
    "small": "small",   
    "medium": "medium",
    "large" : "large",
    "huge" : "huge",
    "giga" : "giga",
    "tera" : "tera"
    } 

CONST_DEFAULT_OFFSET = 0
CONST_DEFAULT_RETRY = 3
CONST_DEFAULT_TIMEOUT = 30
CONST_DEFAULT_REPEAT = False

# This can go multi-class, be aware of thread safety !
# Note : There MUST be a watchdog thread to monitor for global agent events, else we will become orphaned

class AgentRunner:
    def __init__(self):
        self.downloadclients = [] 
        self.created_time = datetime.now()

        log_writer.log(f"AgentRunner.__init__: created={self.created_time.strftime('%Y-%m-%d %H:%M:%S')}", logging.INFO )

#watchdog, looking for global events to control threads in this class
    def __start_watchdog(self):
        try:
            _self_thread_name = threading.current_thread().name

            if _self_thread_name:
                self._stop_watchdog = threading.Event()
                self._watchdog = threading.Thread(target=self.__run_watchdog, name=f"{_self_thread_name}._watchdog")
                self._watchdog.start()
            #endIf
        except Exception as e:
            #to-do: throwing exception, but this needs better handling of why on __init__
            cls_agent.Exception.throw(error=(f"AgentRunner.__start_watchdog: {e}"))
        #endTry

    def __run_watchdog(self):
        log_writer.log(f"AgentRunner.__run_watchdog: Watchdog thread started",logging.DEBUG)
        
        while not self._stop_watchdog.is_set():
            if cls_agent.is_Agent_Shutdown() or cls_agent.is_Threads_Terminate_Requested():
                self._stop_watchdog.set()
                self.terminate()
            time.sleep(1)
        #endWhile

        log_writer.log(f"AgentRunner.__run_watchdog: Watchdog thread exited, killing class",logging.DEBUG)

        self.terminate

    def exec_upload_task(self, task):
        pass

    def exec_quote_task(self, task):
        pass
    
    def exec_download_task(self, task):
        self.__start_watchdog()

        log_writer.log(f"AgentRunner.exec_download_task: Start | task_ref:{task.task_ref}",logging.DEBUG)

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
        
        log_writer.log(f"AgentRuner.exec_download_task: Processing | task_ref:{task.task_ref} | filesize:{filesize} | workers:{workers}",logging.DEBUG)
        
        _threads = []
        
        #spawn the thread workers
        for i in range(workers):
            _downloadclient = AgentDownloader()
            _downloadclient_thread = threading.Thread(target=_downloadclient.download, args=(filesize, offset, timeout, retry, repeat,), name=f"Thread-2(AgentRunner.Download).{task.task_ref}")
            _downloadclient_thread.setDaemon(True)
            _threads.append(_downloadclient_thread)
            _downloadclient_thread.start()
                
        _thread_count = len(_threads)

        while len(_threads) > 0 and not self._stop_watchdog.is_set():
            for thread in _threads:
                if thread.is_alive():
                    thread.join(timeout=1)
                else:
                    _thread_count=_thread_count-1   
                #endIf
                if _thread_count == 0:
                    break
                #endIf
            #endFor
            if _thread_count == 0:
                self._stop_watchdog.set()
                log_writer.log(f"AgentRunner.exec_download_task: Control thread loop exited | task_ref:{task.task_ref}",logging.DEBUG)
        #endWhile

        log_writer.log(f"AgentRunner.exec_download_task: Finished | task_ref:{task.task_ref}",logging.DEBUG)

    def terminate(self):
        log_writer.log(f"AgentRunner.Terminate: Deleting Self", logging.DEBUG)
        
        del self
