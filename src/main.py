"""
===============================================================================
Title : main.py

Description : Entry point for the agent

===============================================================================
"""

# IMPORTS --------------------------------------------------------------------

from autonomi import ant_client
import logging
from log import LogWriter
from scheduler import ScheduleManager
import sys
import version
from agent_performance import Performance 
            

# DEFINITIONS ------------------------------------------------------------------


# MAIN -------------------------------------------------------------------------
if __name__ == "__main__":
    
    #Switch logging to file ON
    log_writer = LogWriter(log_to_file=True)

    #Build Information
    log_writer.log(f"Build Name: {version.BUILD_NAME}", logging.INFO)
    log_writer.log(f"Build Version: {version.BUILD_VERSION}", logging.INFO)
    log_writer.log(f"Build Commit Hash: {version.COMMIT_HASH}", logging.INFO)
    log_writer.log(f"Build Date: {version.BUILD_DATE}", logging.INFO)

    #Detect if client can be found, else terminate
    client = ant_client()
    ant_version = client.version()
    if "not_found" in ant_version:
       log_writer.log(f"The 'autonomi' client command was not found. Have you installed it ?", logging.ERROR )
       sys.exit(1)
    else:
        log_writer.log(f"Found Client: {ant_version}", logging.INFO)
    #endIfElse

    #Create an instance of global test schedule
    schedule_manager = ScheduleManager()
    schedule_manager.initiate()
    schedule_manager.fetch_tasks()

    #create performance global instance
    perf = Performance()

    log_writer.log(f"Agent Scheduler Threads for (ScheduleManager) and (TaskManager) started", logging.INFO)
    log_writer.log(F"Press >> q << to terminate agent.", logging.INFO)

    #To-Do: Needs replacing with a service handler, to allow nohup and also register a kill signal
    while True:
        user_input = input("")
        if user_input.lower() == 'q':
            schedule_manager.terminate()
            perf.shutdown()
            log_writer.log(f"Scheduler Threads terminated and Agent is stopped.", logging.INFO)
            break
        #endIf
    #endWhile
    sys.exit(None)