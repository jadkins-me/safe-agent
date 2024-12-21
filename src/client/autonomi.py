"""
===================================================================================================
Title : autonomi.py

Description : Wrapper around binaries

Copyright 2024 - Jadkins-Me

This Code/Software is licensed to you under GNU AFFERO GENERAL PUBLIC LICENSE (GPL), Version 3
Unless required by applicable law or agreed to in writing, the Code/Software distributed
under the GPL Licence is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. Please review the Licences for the specific language governing
permissions and limitations relating to use of the Code/Software.

===================================================================================================
"""

import subprocess
import os
import tempfile
import inspect
import logging
import hashlib
from log import LogWriter
from application import Agent
from type_def import typedef_Agent_Client_Response
from client import autonomi_messages

cls_agent = Agent()
log_writer = LogWriter()

class ant_client:
   def ___init___(self):
      # BOILER: todo
      pass

   def __del__(self):
      #todo: wrong place
      log_writer.log(f"Ant_Client:download: Finished",logging.DEBUG)        
   
   def __get_temp_filepath (self,filename):
      if filename:
         prefix = filename.lower()
      else:
         prefix ="unknown"

      temp_file_name = os.path.join( cls_agent.Configuration.CLIENT_DOWNLOAD_PATH, f"{prefix}_{next(tempfile._get_candidate_names())}" )
      return (temp_file_name)
   
   def __del_temp_filepath (self,filename):
      try: 
         if os.path.isfile(filename): 
            os.remove(filename) 
         #endIf
      except Exception as e: 
         log_writer.log(f"ant_client.__del_temp_filepath: Error occurred while deleting {filename}: {e}",logging.DEBUG)
   
   def quote(self, filename, timeout=30):
      # BOILER: todo
      pass

   def download(self, file_address, timeout):

      # BOILER: todo
      log_writer.log(f"ant_client:download: Start | file: {file_address.name} | address: {file_address.address}",logging.DEBUG)        

      temp_file_name = self.__get_temp_filepath(file_address.name)
      temp_file_name_log = cls_agent.Configuration.CLIENT_LOGGING_PATH

      #pass custom peers from environment
      if cls_agent.Configuration.CLIENT_PEERS:
         command = [ 
            './bin/ant', 
            '--peer', str(cls_agent.Configuration.CLIENT_PEERS),
            '--timeout', str(timeout), 
            '--log-output-dest', 
            temp_file_name_log, 
            'file', 
            'download', 
            file_address.address, 
            temp_file_name 
         ]
      else:
         command = [ 
            './bin/ant', 
            '--timeout', str(timeout), 
            '--log-output-dest', 
            temp_file_name_log, 
            'file', 
            'download', 
            file_address.address, 
            temp_file_name 
         ]
      #endIf

      _return_results = typedef_Agent_Client_Response

      try:
         #needs wrapping in a timer

         _return_results.client_started = True
         #WARNING ! shell=False is a safety measure to minimize XSS injections, don't change unless you know what the implications are
         process = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
         
         #wait         
         process.wait() 
         
         #todo: needs pushing on a queue to handle threads

         # apture the output and errors 
                    
         stdout, stderr = process.communicate()

         _stderr_break = False
         
         a = autonomi_messages._error_messages

         #pass stderr
         for error, tag in autonomi_messages._error_messages.items(): 
            if error in stderr.lower(): 
               _stderr_break = True
               if tag == autonomi_messages._error_network:
                  _return_results.network_error = True
               elif tag == autonomi_messages._error_client:
                  _return_results.client_error = True
               
               log_writer.log(f"ant_client.download: processing stderr found a match | _return_tag={tag}",logging.DEBUG)
            #endIf
            if _stderr_break:
               break
         #endFor

      except subprocess.TimeoutExpired as e:
         _return_results.client_error = True
         log_writer.log(f"ant_client.download: client process was timed out",logging.DEBUG)
      except subprocess.CalledProcessError as e:
         _return_results.unknown_error = True
         log_writer.log(f"ant_client.download: Unknown exception occured in client process",logging.DEBUG)
      except FileNotFoundError:  #to-do : should be using common dictionary
         cls_agent.Exception.throw(error=(f"{self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: File Not Found"))
         return "Error: not_found" # don't change the wording as we look for a match in other modules
      finally:
         if not _stderr_break:
            log_writer.log(f"ant_client.download: client process exit clean",logging.DEBUG)
            _return_results.client_ok = True
      #endTry

      #todo: process md5 - and check the file downloaded first - if file exists else we error, and waste time 
      if file_address.md5:
         _return_results.md5_checked = True
         
         file_md5 = self.verify_md5(temp_file_name,file_address.md5)
         if file_md5:
            _return_results.md5_valid = True

      #endIf

      #todo : not the right place for this, it doesn't handle exception cleanup
      self.__del_temp_filepath(filename=temp_file_name)

      return _return_results

##to-do : new hashed this is low   
   def calculate_md5(self,file_path): 
      hasher = hashlib.md5() 

      try:
         with open(file_path, 'rb') as file: 
            while chunk := file.read(8192): 
               hasher.update(chunk) 
      except Exception as e:
         return None
      return hasher.hexdigest() 
   
   def verify_md5(self,file_path, supplied_hash): 
      file_md5 = self.calculate_md5(file_path) 
      return file_md5 == supplied_hash
   
   def upload(self, filename, timeout=30):
      # BOILER: todo
      pass

   def version(self):
      try:
         result = subprocess.run(['./bin/ant', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
         return result.stdout.strip()
      except subprocess.CalledProcessError as e:
         return f"Error: {e.stderr.strip()}"
      except FileNotFoundError:
         cls_agent.Exception.throw(error=(f"{self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: File Not Found"))
         return "Error: not_found" # don't change the wording as we look for a match in other modules
