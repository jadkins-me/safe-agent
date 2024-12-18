"""
===================================================================================================
Title : agent_download.py

Description : handler to download logic

Copyright 2024 - Jadkins-Me

This Code/Software is licensed to you under GNU AFFERO GENERAL PUBLIC LICENSE (GPL), Version 3
Unless required by applicable law or agreed to in writing, the Code/Software distributed
under the GPL Licence is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. Please review the Licences for the specific language governing
permissions and limitations relating to use of the Code/Software.

===================================================================================================
"""

import inspect
import logging
from log import LogWriter
from dataclasses import dataclass
from client.autonomi import ant_client
from agent.agent_performance import Performance
from application import Agent
from agent.agent_limiter import Limiter
import csv 
import os 
import random 
import requests 
import time 
import json
import kill_switch
from agent.agent_helper import Utils
from type_def import typedef_Agent_Client_Response

cls_agent = Agent()

#logging handler
log_writer = LogWriter()

#get a handle to kill switch detection
killswitch_checker = kill_switch.GitHubRepoIssuesChecker()

#This can go MultiClass, be aware of thread safety !
class AgentDownloader:
    @dataclass 
    class file:
        address: str = ""
        name: str = ""
        md5: str = ""
    
    def __init__(self):
        #spawn a handler to ant client wrapper
        self.ant_client = ant_client()

        #rate limit handler
        self.rate_limit = Limiter()
    
#-----> Cache handling of files that can be processed in the CSV file ----------------------------------------
    def __download_csv(self): 
        response = requests.get(cls_agent.Configuration.CSV_URL) 
        response.raise_for_status() 
        with open(cls_agent.Configuration.CACHE_FILE, 'w', newline='') as file: 
            file.write(response.text) 
        with open(cls_agent.Configuration.CACHE_INFO_FILE, 'w') as info_file: 
            cache_info = {'download_time': time.time()} 
            json.dump(cache_info, info_file) 
                
    def __is_cache_valid(self): 
        if os.path.exists(cls_agent.Configuration.CACHE_FILE) and os.path.exists(cls_agent.Configuration.CACHE_INFO_FILE): 
            with open(cls_agent.Configuration.CACHE_INFO_FILE, 'r') as info_file: 
                cache_info = json.load(info_file) 
                if time.time() - cache_info['download_time'] < cls_agent.Configuration.CACHE_TIME: 
                    return True
                #endIf 
                return False 
            #endWith
        #endIf

    def get_file(self,filesize): 
        if not self.__is_cache_valid(): 
            self.__download_csv()
        #endIf
            
        with open(cls_agent.Configuration.CACHE_FILE, newline='') as csvfile: 
            reader = csv.DictReader(row for row in csvfile if not row.startswith('#')) 
            matching_rows = [row for row in reader if row.get('fileSize') == filesize] 
            if matching_rows: 
                return random.choice(matching_rows) 
            else: 
                return None
            #endIf
        #endWith

    def __get_file_address(self, filesize): 
        file_dict = self.get_file(filesize) 
        if file_dict: 
            return self.file( 
                address=file_dict['address'], 
                name=file_dict['name'], 
                md5=file_dict['md5'] 
            ) 
        return None

# -----> Download --------------------------------------------------------------
    def download (self, 
                  filesize: str, 
                  offset: int, 
                  timeout: int, 
                  retry: int, 
                  repeat: bool) -> None:
        
        log_writer.log(f"AgentDownloader:download: Start | filesize:{filesize} | Repeating:{repeat}",logging.DEBUG)

        # ensure we go through one itteration
        repeat_loop = True  

        #python type casting on how it handles boolean =o
        #todo: need to handle that when passing XML input file, this is the wrong place
        repeat = repeat.lower() in ['true', '1', 'yes']
        if offset in ('false','0'): 
            offset = 0
        else:
            offset = int(offset)
        #endIf

        # Mimicking do-while loop :(
        while repeat_loop: 
            #*** Start Download

            #push into rate limiter, on true we are overloaded so break
            rl = self.rate_limit.is_ratelimit_download()
            if rl:
                break

            #start a performance instance
            _download_results = Performance.TestResults(test_type="download")
            _download_results.file_size = filesize

            #get address of a file from CSV to download
            file_address = self.__get_file_address(str.lower(filesize)) 
            
            if file_address:
                if isinstance(offset, int) and int(offset) > 0:
                    #call the offset, and sleep for this long
                    time_to_sleep = Utils.offset(offset_minutes=int(offset))
                    log_writer.log(f"AgentDownloader.download: offset is set | time_to_sleep {time_to_sleep}", logging.DEBUG)
                    time.sleep(time_to_sleep)
                #endIf

                #push our test instance, into a test we are about to run
                _performance = Performance.Test(_download_results.test_type) 
                                
                #push timer start
                _performance.start_timer()
                _response = typedef_Agent_Client_Response() 
                
                try:
                    #custom type for client response handling - strong typing needed #todo
                    _response: typedef_Agent_Client_Response = self.ant_client.download (file_address,timeout)
                except Exception as e:
                    #to:do need to fill in _response
                    pass

                _performance.stop_timer()
                #end timer              

                #todo: populate actual data - data types need defining
                _download_results.cli_err = _response.client_error
                _download_results.md5 = _response.md5_valid
                _download_results.un_err = _response.unknown_error

                _performance.add_results(_download_results)
       
            else: 
                #need to handle this somehow...
                log_writer.log(f"> > {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: Unable to find a file in CSV matching {filesize}",logging.ERROR)

                #throw and exception, as we can't run this task
                #to-do: need a more graceful way to just block download tasks
                cls_agent.Exception.throw(error="AgentDownloader.download: Unable to find a file in CSV matching file size")
            #endIfElse

            #*** Finish Download
            # Update condition if we have been requested to loop
            if bool(repeat):
                #check to see if we should be cancelling due to kill switch
                if killswitch_checker.check_for_kill_switch()[0]: #need a try catch in the kill switch class
                    repeat_loop = False
                    break
                elif Utils.scheduler_no_tasks_window():
                    repeat_loop = False
                    break
                #endIfElse

                #enfore a sleep, so this thread can yield
                time.sleep(cls_agent.Configuration.DOWNLOAD_YIELD_SECS)                 
            else:
                #download was not requested to repeat
                repeat_loop = False
            #endIf
        #endWhile

        #release test object
        test_results = None

        log_writer.log(f"AgentDownloader:download: Finished",logging.DEBUG)

        del self