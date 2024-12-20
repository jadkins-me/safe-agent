"""
===================================================================================================
Title : scheduler.py

Description : The schedule manager object, responsbile for spawning the tasks

Copyright 2024 - Jadkins-Me

This Code/Software is licensed to you under GNU AFFERO GENERAL PUBLIC LICENSE (GPL), Version 3
Unless required by applicable law or agreed to in writing, the Code/Software distributed
under the GPL Licence is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. Please review the Licences for the specific language governing
permissions and limitations relating to use of the Code/Software.

===================================================================================================
"""

import schedule
import inspect
import time
import threading
from application import Agent
import logging
from agent.agent_runner import AgentRunner
from tasks import Agent_Task
import kill_switch
from log import LogWriter
from agent.agent_helper import Utils
from tabulate import tabulate

#get a handle to logging class
log_writer = LogWriter()
cls_agent = Agent()

#get a handle to kill switch detection
killswitch_checker = kill_switch.GitHubRepoIssuesChecker()

#get a handle to helper utils
helper = Utils()

# Notes : This is a single instance class, so ensure that is enforced.
class ScheduleManager:
     #Ensure this is a single instance class
    _instance = None

    def __new__(cls, *args, **kwargs): 
        if not cls._instance: cls._instance = super(ScheduleManager, cls).__new__(cls, *args, **kwargs) 
        return cls._instance 
    
    def __init__(self): 
        if not hasattr(self, 'initialized'): 
            # Ensure __init__ runs only once 
            self.initialized = True
            self._instance = False  # Allow schedule setup only once, and define threads

            self.tasks = []         # holds the tasks we have spawned from the test plan
            self.agent_runners = [] # Store references to AgentRunner instances

            #Schedule Manager (SM) Schedule used for running jobs - can be paused, and cleared
            self._paused = True 
            self._stop_eventSM = threading.Event()
            self._schedulerSM = schedule.Scheduler()

            #Task Manager (TM) Schedule used solely for downloading jobs to run from github
            self._stop_eventTM = threading.Event()
            self._schedulerTM = schedule.Scheduler()
        #endIf
    
    def __convert_to_colon_format(self, minutes_string):
        padded_minutes = f"{int(minutes_string):02d}"
        return f":{padded_minutes}"

    def __add_task(self, task):
        if self.task_already_scheduled(self.__convert_to_colon_format(task.time_period)):
            log_writer.log(f"Task already scheduled at {self.__convert_to_colon_format(task.time_period)}", logging.ERROR)
            return
        if task.test_type.lower() == "download":
            self._schedulerSM.every(1).minute.do(self.__downloadtask_schedule, task)
            #self._schedulerSM.every().hour.at(self.__convert_to_colon_format(task.time_period)).do(self.__downloadtask_schedule, task)
            self.tasks.append((task, "download", self.__convert_to_colon_format(task.time_period)))
        elif task.test_type.lower() == "quote":
            self._schedulerSM.every(2).minutes.do(self.__quotetask_schedule, task)
            #self._schedulerSM.every().hour.at(self.__convert_to_colon_format(task.time_period)).do(self.__quotetask_schedule, task)
            self.tasks.append((task, "quote", self.__convert_to_colon_format(task.time_period)))
        elif task.test_type.lower() == "upload":
            self._schedulerSM.every().hour.at(self.__convert_to_colon_format(task.time_period)).do(self.__uploadtask_schedule, task)
            self.tasks.append((task, "upload", self.__convert_to_colon_format(task.time_period)))
        else:
            log_writer.log(f"Unknown test type: {task.test_type}", logging.ERROR)
            
    # Fetch_Tasks will query the source, and populate a TASKS object will all the tasks to execute
    def fetch_tasks(self):
        log_writer.log(f"Fetching tasks and jobs from github XML and updating schedule",logging.INFO)    
 
        #pause any existing schedules, and clear them
        self.pause_schedule()
        self.clear_schedule()
 
        #if killswitch is active, then we don't process any TASKS and we wait...      
        killswitch_found, datetime = killswitch_checker.check_for_kill_switch()
        if killswitch_found:
            log_writer.log(f"Kill-switch ON, test paused by github issue created {datetime}, agent active.",logging.WARNING)
        else:
            tasks = Agent_Task.fetch_and_parse_xml(cls_agent.Configuration.SCHEDULER_URL)

            # Collect data for table, and store it in tabulate format 
            table_data = []

            for task in tasks:
                table_data.append( {
                    "Task": f"{task.task_ref}",
                    "Mins" : f"{task.time_period}",
                    "Worker": f"{task.test_options.get('workers', None)}", 
                    "Repeat": f"{task.test_options.get('repeat', False)}",
                    "Offset": f"{task.test_options.get('offset', None)}",
                    "Type": f"{task.test_type}", 
                    "Description": f"{task.description}" 
                })

                self.__add_task(task)
            #EndFor

            # Create a nice looking table 
            table = tabulate(table_data, headers="keys", tablefmt="grid", numalign="centre")

            # todo - logger doesnt support tabulate format
            print(f"{table}")

            self.__purge_envionment()

            self.resume_schedule()
        #EndIfElse

# ----> DOWNLOAD TASK SCHEDULER <--------------------------------------------------------------------------------------------------
    def __downloadtask_schedule(self, task):
        log_writer.log(f"> > {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: {task.task_ref}", logging.DEBUG )

        if Utils.scheduler_no_tasks_window():
            log_writer.log(f"> > {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: _scheduler_no_tasks_window: TRUE", logging.DEBUG )
            #We can't execute this schedule, as we are in a no-tasks window
        elif killswitch_checker.check_for_kill_switch()[0]:
            log_writer.log(f"> > {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: check_for_kill_switch: TRUE", logging.DEBUG )
            #We can't execute this schedule, kill switch is active
        else:
            try:
                #pass the task over to the Agent Runner to spawn the workers
                agent_runner = AgentRunner()
                self.agent_runners.append(agent_runner) # Keep track of AgentRunner instances 
                agent_runner.exec_download_task(task)
            except Exception as e:
                log_writer.log(f"> > {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: {e}", logging.ERROR)
            #endTry
        #endIfElse    
        
        log_writer.log(f"< < {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: return: NONE", logging.DEBUG )

# ----> QUOTE TASK SCHEDULER <--------------------------------------------------------------------------------------------------
    def __quotetask_schedule(self, task):
        log_writer.log(f"> > {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: {task.task_ref}", logging.DEBUG )

        if Utils.scheduler_no_tasks_window():
            log_writer.log(f"> > {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: _scheduler_no_tasks_window: TRUE", logging.DEBUG )
            #We can't execute this schedule, as we are in a no-tasks window
        elif killswitch_checker.check_for_kill_switch()[0]:
            log_writer.log(f"> > {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: check_for_kill_switch: TRUE", logging.DEBUG )
            #We can't execute this schedule, kill switch is active
        else:
            try:
                #pass the task over to the Agent Runner to spawn the workers
                agent_runner = AgentRunner()
                self.agent_runners.append(agent_runner) # Keep track of AgentRunner instances 
                agent_runner.exec_quote_task(task)
            except Exception as e:
                log_writer.log(f"> > {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: {e}", logging.ERROR)
            #endTry
        #endIfElse    
        
        log_writer.log(f"< < {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: return: NONE", logging.DEBUG )

# ----> UPLOAD TASK SCHEDULER <--------------------------------------------------------------------------------------------------
    def __uploadtask_schedule(self, task):
        log_writer.log(f"> > {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: {task.task_ref}", logging.DEBUG )

        if Utils.scheduler_no_tasks_window():
            log_writer.log(f"> > {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: _scheduler_no_tasks_window: TRUE", logging.DEBUG )
            #We can't execute this schedule, as we are in a no-tasks window
        elif killswitch_checker.check_for_kill_switch()[0]:
            log_writer.log(f"> > {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: check_for_kill_switch: TRUE", logging.DEBUG )
            #We can't execute this schedule, kill switch is active
        else:
            try:
                #pass the task over to the Agent Runner to spawn the workers
                agent_runner = AgentRunner()
                self.agent_runners.append(agent_runner) # Keep track of AgentRunner instances 
                agent_runner.exec_upload_task(task)
            except Exception as e:
                log_writer.log(f"> > {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: {e}", logging.ERROR)
            #endTry
        #endIfElse    
        
        log_writer.log(f"< < {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: return: NONE", logging.DEBUG )

# ----> LIST TASK <-----------------------------------------------------------------------------------------------------------
    def list_schedules(self):
        if not self.tasks:
            print("No tasks scheduled.")
        else:
            for task in self.tasks:
                log_writer.log(f"Task: {task}")

    def task_already_scheduled(self, time):
        for _, _, scheduled_time in self.tasks:
            if scheduled_time == time:
                return True
        return False

    def __run_pendingSM(self):
        while not self._stop_eventSM.is_set():
            if not self._paused:
                self._schedulerSM.run_pending()
            time.sleep(1)

    def __run_pendingTM(self):
        while not self._stop_eventTM.is_set():
            self._schedulerTM.run_pending()
            time.sleep(1)        

    def __purge_envionment(self):
        #todo : routines to clear out old test runs, logs, and cache
        pass

    def initiate(self):
        if not self._instance:
            self.scheduler_threadSM = threading.Thread(target=self.__run_pendingSM,name="Thread-1(Scheduler.ScheduleManager.SM)")
            self.scheduler_threadSM.start()
            self._paused = False

            self.scheduler_threadTM = threading.Thread(target=self.__run_pendingTM,name="Thread-1(Scheduler.ScheduleManager.TM)")
            self.scheduler_threadTM.start()

            #to-do: change schedule to every minute for fast refresh, and ability to invoke refresh with rate limit
            self._schedulerTM.every().hour.at(cls_agent.Configuration.SCHEDULER_CHECK).do(self.fetch_tasks)
            #self._schedulerTM.every(1).minutes.do(self.fetch_tasks)
            log_writer.log(f"Starting TM Scheduler to check github for new jobs at {cls_agent.Configuration.SCHEDULER_CHECK} every hour", logging.INFO)
            self._instance = True      
        else:
            log_writer.log(F"Scheduler intiate has been called more than once, this is not supported.", logging.ERROR)
        #endIfElse

    def terminate(self):
        self._stop_eventSM.set()
        self._stop_eventTM.set()
        self.scheduler_threadSM.join()
        self.scheduler_threadTM.join()
        log_writer.log(f"Agent Scheduler TM & SM received Terminate signal -", logging.WARNING)

        # Ensure all AgentRunner instances are cleaned up 
        for runner in self.agent_runners: 
            runner.cleanup() 
        log_writer.log(f"Agent Scheduler - AgentRunner instances cleaned up", logging.INFO)

    def pause_schedule(self):
        self._paused = True
        log_writer.log(f"Agent Scheduler SM received pause signal ||", logging.INFO)

    def resume_schedule(self):
        self._paused = False
        log_writer.log(f"Agent Scheduler SM received resume signal +", logging.INFO)

    def clear_schedule(self):
        self._schedulerSM.clear()
        self.tasks = []
        log_writer.log(f"Agent Scheduler SM received clear signal >|", logging.INFO)