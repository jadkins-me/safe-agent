"""
===============================================================================
Title : autonomi.py

Description : Wrapper around pre-compiled binaries

===============================================================================
"""

import subprocess
import os
import inspect
import logging
from log import LogWriter
import tempfile
from constants import Exception

log_writer = LogWriter()

class ant_client:
   def ___init___(self):
      # BOILER: todo
      self.except_handler = Exception()
      pass
   
   def __get_temp_filepath (self,filename):
      if filename:
         prefix = filename.lower()
      else:
         prefix ="unknown"

      custom_path = "./cache/downloads"
      temp_file_name = os.path.join( custom_path, f"{prefix}_{next(tempfile._get_candidate_names())}" )
      return (temp_file_name)
   
   def quote(self, filename, timeout=30):
      # BOILER: todo
      pass
   def download(self, file_address, timeout):
      error_messages = { 
         "could not connect to enough peers in time": "error:network"
      }
      error_unknown = {"error:unknown"}

      # BOILER: todo
      log_writer.log(f"< < {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: file: {file_address.name}, address: {file_address.address}, md5: {file_address.md5}",logging.INFO)        

      temp_file_name = self.__get_temp_filepath(file_address.name)
      temp_file_name_log = "./cache/log/"

      command = [ 
         './bin/autonomi', 
         '--timeout', str(timeout), 
         '--log-output-dest', 
         temp_file_name_log, 
         'file', 
         'download', 
         file_address.address, 
         temp_file_name 
      ] 
      
      try:
         #WARNING ! shell=False is a safety measure to minimize XSS injections, don't change unless you know what the implications are
         result = subprocess.run( command, shell=False,check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True )

         #to-do: need to handle file cleanup chore
         log_writer.log(f"{result.stdout.strip()}",logging.INFO)
         return result.stdout.strip()
      except subprocess.CalledProcessError as e:
         err_tag=error_unknown
         output = (e.stdout + e.stderr).lower() 
         for error, action in error_messages.items(): 
            if error in output: 
               err_tag = action
         return (err_tag)
      except FileNotFoundError:  #to-do : should be using common dictionary
         self.except_handler.throw(error=(f"{self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: File Not Found"))
         return "Error: not_found" # don't change the wording as we look for a match in other modules


      pass
   def upload(self, filename, timeout=30):
      # BOILER: todo
      pass
   def version(self):
      try:
         result = subprocess.run(['./bin/autonomi', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
         return result.stdout.strip()
      except subprocess.CalledProcessError as e:
         return f"Error: {e.stderr.strip()}"
      except FileNotFoundError:
         self.except_handler.throw(error=(f"{self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: File Not Found"))
         return "Error: not_found" # don't change the wording as we look for a match in other modules
