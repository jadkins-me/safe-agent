"""
===============================================================================
Title : agent_download.py

Description : handler to download logic

===============================================================================
"""
import inspect
import logging
import constants
from log import LogWriter
from dataclasses import dataclass
from autonomi import ant_client
from agent_performance import Performance
import csv 
import os 
import random 
import requests 
import time 
import json

class AgentDownloader:
    @dataclass 
    class file:
        address: str = ""
        name: str = ""
        crc: str = ""
    
    def __init__(self):
        self.ant_client = ant_client()
        pass

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
                return False 
    
    def get_file(self,filesize): 
        if not self.__is_cache_valid(): 
            self.__download_csv() 
            
        with open(constants.CACHE_FILE, newline='') as csvfile: 
            reader = csv.DictReader(csvfile) 
            matching_rows = [row for row in reader if row.get('fileSize') == filesize]
            if matching_rows: 
                return random.choice(matching_rows) 
            else: 
                return None

    def __get_file_address(self, filesize): 
        file_dict = self.get_file(filesize) 
        if file_dict: 
            return self.file( 
                address=file_dict['address'], 
                name=file_dict['name'], 
                crc=file_dict['crc'] 
            ) 
        return None

    def download (self,filesize,offset,timeout,retry,repeat):
        log_writer.log(f"> > {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: filesize:{filesize}",logging.INFO)        

        test_results = Performance.TestResults(test_type="download")

        file_address = self.__get_file_address(str.lower(filesize)) 
        
        if file_address: 
            
            test = Performance.Test(test_results.test_type) 
               
            #push timer start
            test.start_timer()
            #do a retry loop
            response = self.ant_client.download (file_address,timeout)
            #if response is soft fail - retry
            test.stop_timer()
            #end timer
            #push performance stats
            test_results.file_size = filesize

            test.add_results(test_results)

        else: 
            #need to handle this somehow...
            log_writer.log("No matching file found", logging.INFO)
        pass

    def cleanup (self):
        del self

log_writer = LogWriter(log_to_file=True)