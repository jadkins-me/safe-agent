"""
===============================================================================
Title : tasks.py

Description : Task loader and task definition

===============================================================================
"""
import constants
import xml.etree.ElementTree as ET
import requests
import logging
from log import LogWriter

class Agent_Task:
    def __init__(self, task_ref, description, time_period, time_offset, test_type, test_options):
        self.task_ref = task_ref
        self.description = description
        self.time_period = time_period
        self.time_offset = time_offset
        self.test_type = test_type
        self.test_options = test_options

    def __repr__(self):
        return (f"Task(task_ref={self.task_ref}, description={self.description}, "
                f"time_period={self.time_period}, time_offset={self.time_offset}, "
                f"test_type={self.test_type}, test_options={self.test_options})")

    def fetch_and_parse_xml(url):
        try:
            response = requests.get(constants.SCHEDULER_URL)
            response.raise_for_status()  # Raise an exception if the request fails
        except requests.exceptions.RequestException as e:
            log_writer.log(f"Error fetching the XML data: {e}", logging.ERROR)
            return []
        #endTry

        try:
            root = ET.fromstring(response.text)
        except ET.ParseError as e:
            log_writer.log(f"Error parsing the XML data: {e}", logging.ERROR)
            return []
        #endTry

        tasks = []

        for task in root.findall('Task'):
            try:
                task_ref = task.find('TaskRef').text
                description = task.find('Description').text
                time_period = task.find('TimePeriod').text
                time_offset = task.find('TimeOffset').text
                test_type = task.find('TestType').text

                test_options = {}
                for option in task.find('TestOptions').findall('Option'):
                    test_options[option.attrib['key']] = option.attrib['value']
                #endFor

                tasks.append(Agent_Task(task_ref, description, time_period, time_offset, test_type, test_options))
            except AttributeError as e:
                log_writer.log(f"Error processing a task element: {e}",logging.ERROR)
            #endTry
        #endFor
        
        return tasks

log_writer = LogWriter(log_to_file=True)