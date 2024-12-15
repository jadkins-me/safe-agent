"""
===================================================================================================
Title : main.py

Description : Entry point for the agent

Copyright 2024 - Jadkins-Me

This Code/Software is licensed to you under GNU AFFERO GENERAL PUBLIC LICENSE (GPL), Version 3
Unless required by applicable law or agreed to in writing, the Code/Software distributed
under the GPL Licence is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. Please review the Licences for the specific language governing
permissions and limitations relating to use of the Code/Software.

===================================================================================================
"""

# IMPORTS --------------------------------------------------------------------

from autonomi import ant_client
import logging
from log import LogWriter
from scheduler import ScheduleManager
import sys
import version
import threading 
import queue 
import tty 
import termios 
import time
from agent_performance import Performance
from constants import Exception , Configuration          

# DEFINITIONS ------------------------------------------------------------------
def getch(): 
    fd = sys.stdin.fileno() 
    old_settings = termios.tcgetattr(fd) 
    try: 
        tty.setraw(fd) 
        ch = sys.stdin.read(1) 
    finally: 
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings) 
        return ch 

def read_input(): 
    while True: 
        ch = getch() 
        input_queue.put(ch) 
        if ch == 'q': 
            break

# MAIN -------------------------------------------------------------------------
if __name__ == "__main__":
    
    #handler for the main input loop
    input_queue = queue.Queue()
    
    #exception handler class init
    except_handler = Exception()

    #singleton class to configure constants from env, config file #to-do
    _main_config = Configuration()
    _main_config.load() #todo
    
    #singleton class logging thread
    log_writer = LogWriter()

    #Build Information
    log_writer.log(f"Build Name: {version.BUILD_NAME}", logging.INFO)
    log_writer.log(f"Build Version: {version.BUILD_VERSION}", logging.INFO)
    log_writer.log(f"Build Commit Hash: {version.COMMIT_HASH}", logging.INFO)
    log_writer.log(f"Build Date: {version.BUILD_DATE}", logging.INFO)

    #Detect if client can be found, else terminate
    client = ant_client()
    ant_version = client.version()
    if "not_found" in ant_version:
       log_writer.log(f"The 'autonomi' client command was not found. Have you installed it ?", logging.FATAL )
       sys.exit(1)
    else:
        log_writer.log(f"Found Client: {ant_version}", logging.INFO)
    #endIfElse
    client = None

    #Create an instance of global test schedule, which will chain all the worker threads
    schedule_manager = ScheduleManager()
    schedule_manager.initiate()
    schedule_manager.fetch_tasks()  #todo - we manually call the fetch tasks here - this shouldn't be needed

    #create performance logging and metric global instance
    perf = Performance()

    #Show console update that we are running
    log_writer.log(f"Agent Scheduler Threads for (ScheduleManager) and (TaskManager) started", logging.INFO)
    log_writer.log(F"Press >> q << to terminate agent - (10 second delay)", logging.INFO)

     # Start the input reading thread 
    input_thread = threading.Thread(target=read_input, name="Thread-0(_main.read_input)") 
    input_thread.daemon = True 
    input_thread.start() 

    #Lazy main loop # todo - needs to support service / docker / webapp
    while True: 
        try: 
            user_input = input_queue.get_nowait() 
            if user_input == 'q': 
                schedule_manager.terminate()
                perf.shutdown()
                log_writer.log(f"Scheduler Threads terminated and Agent is stopped.", logging.INFO)
                sys.exit(None)
                #end __main__
            elif user_input == 'f': 
                #to:do - place holder
                pass 
            #endIf
        except queue.Empty: 
            # handle this when no user input - should really be somewhere else
            if except_handler.has_occurred():
                log_writer.log(f"Code exception has occured {except_handler.get}",logging.FATAL)
                sys.exit(1)
                #end __main__ with FATAL exception
        # Sleep for 10 seconds 
        time.sleep(10)