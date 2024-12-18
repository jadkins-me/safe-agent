"""
===================================================================================================
Title : type_def.py

Description : Type Definitions that can be shared by classes

Copyright 2024 - Jadkins-Me

This Code/Software is licensed to you under GNU AFFERO GENERAL PUBLIC LICENSE (GPL), Version 3
Unless required by applicable law or agreed to in writing, the Code/Software distributed
under the GPL Licence is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. Please review the Licences for the specific language governing
permissions and limitations relating to use of the Code/Software.

===================================================================================================
"""

from dataclasses import dataclass

# used in /client/ modules to return response codes
@dataclass
class typedef_Agent_Client_Response: 
    md5_checked : bool = False           # True, md5 hash was checked
    md5_valid   : bool = False           # True, the md5 of the file matches the provided hash
    client_started : bool = False        # True, the wrapped binary was launched
    client_ok      : bool = False        # True, the client ran as expected
    client_killed : bool = False         # True, the client process had to be killed due to hanging, or long running process
    client_error : bool = False          # True, an error occured with the client
    network_error : bool = False         # True, an error occured with the network
    unknown_error : bool = False         # True, an unknown error occured
#endClass 