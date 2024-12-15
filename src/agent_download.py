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
import constants
from log import LogWriter
from dataclasses import dataclass
from autonomi import ant_client
from agent_performance import Performance
from constants import Exception
from agent_limiter import Limiter
import csv 
import os 
import random 
import requests 
import time 
import json
import kill_switch
from agent_helper import Utils

#logging handler
log_writer = LogWriter()

#get a handle to kill switch detection
killswitch_checker = kill_switch.GitHubRepoIssuesChecker()

#exception handler class init
except_handler = Exception()

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
        response = requests.get(constants.CSV_URL) 
        response.raise_for_status() 
        with open(constants.CACHE_FILE, 'w', newline='') as file: 
            file.write(response.text) 
        with open(constants.CACHE_INFO_FILE, 'w') as info_file: 
            cache_info = {'download_time': time.time()} 
            json.dump(cache_info, info_file) 
                
    def __is_cache_valid(self): 
        if os.path.exists(constants.CACHE_FILE) and os.path.exists(constants.CACHE_INFO_FILE): 
            with open(constants.CACHE_INFO_FILE, 'r') as info_file: 
                cache_info = json.load(info_file) 
                if time.time() - cache_info['download_time'] < constants.CACHE_TIME: 
                    return True
                #endIf 
                return False 
            #endWith
        #endIf

    def get_file(self,filesize): 
        if not self.__is_cache_valid(): 
            self.__download_csv()
        #endIf
            
        with open(constants.CACHE_FILE, newline='') as csvfile: 
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
        
        log_writer.log(f"> > {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: filesize:{filesize} Repeating:{repeat}",logging.DEBUG)        

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
            rl = self.rate_limit.push_download()
            if rl:
                break

            #start a performance instance
            test_results = Performance.TestResults(test_type="download")

            #get address of a file from CSV to download
            file_address = self.__get_file_address(str.lower(filesize)) 
            
            if file_address:
                if isinstance(offset, int) and int(offset) > 0:
                    #call the offset, and sleep for this long
                    time_to_sleep = Utils.offset(offset_minutes=int(offset))
                    log_writer.log(f"> > {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: time_to_sleep {time_to_sleep}", logging.DEBUG)
                    time.sleep(time_to_sleep)
                #endIf

                #push our test instance, into a test we are about to run
                test = Performance.Test(test_results.test_type) 
                                
                #push timer start
                test.start_timer()

                response = self.ant_client.download (file_address,timeout)

                #if response is soft fail - retry
                test.stop_timer()
                #end timer
                #push performance stats
                test_results.file_size = filesize #duplicate ?

                test.add_results(test_results)
       
            else: 
                #need to handle this somehow...
                log_writer.log(f"> > {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: Unable to find a file in CSV matching {filesize}",logging.ERROR)

                #throw and exception, as we can't run this task
                #to-do: need a more graceful way to just block download tasks
                except_handler.throw(error="AgentDownloader.download: Unable to find a file in CSV matching file size")
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
                time.sleep(constants.DOWNLOAD_YIELD_SECS)                 
            else:
                #download was not requested to repeat
                repeat_loop = False
            #endIf
        #endWhile

        #release test object
        test_results = None

        self.cleanup()

    def cleanup (self):
        del self