"""
===================================================================================================
Title : autonomi_messages.py

Description : Wrapper around client bianary messages

Copyright 2024 - Jadkins-Me

This Code/Software is licensed to you under GNU AFFERO GENERAL PUBLIC LICENSE (GPL), Version 3
Unless required by applicable law or agreed to in writing, the Code/Software distributed
under the GPL Licence is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. Please review the Licences for the specific language governing
permissions and limitations relating to use of the Code/Software.

===================================================================================================
"""

_error_network ="error:network"
_error_client = "error:client"

_error_messages = { 
    "could not connect to enough peers in time": f"{_error_network}",
    "failed to connect to network": f"{_error_network}",
    "general networking error" : f"{_error_network}"
}