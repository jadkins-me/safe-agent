"""
===============================================================================
Title : agent_performance.py

Description : logging and processing of performance stats

===============================================================================
"""

# reference from other objects with
# from performance import Performance 
# perf = Performance()

import time
import os
import threading
import logging
import datetime
import inspect
from log import LogWriter
from collections import defaultdict
from typing import Optional

class Performance:
    #Ensure this is a single instance class
    _instance = None
    #to-do: this is a mess, need to rationalize
    mem_metrics = []
    metrics_file = "./cache/metrics/metrics.csv"
    metrics_summary_file = "./cache/metrics/summary.csv"
    perf_influxdb = "_ant_agent"
    perf_influxdb_summary = "".join([perf_influxdb, "_smry"])
    
    def __new__(cls, *args, **kwargs): 
        if not cls._instance: cls._instance = super(Performance, cls).__new__(cls, *args, **kwargs) 
        return cls._instance 
    
    def __init__(self): 
        if not hasattr(self, 'initialized'): 
            # Ensure __init__ runs only once 
            self.initialized = True 
            # Initialize stuff here !! TO-DO
            os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True) 
            os.makedirs(os.path.dirname(self.metrics_summary_file), exist_ok=True) 
            self.flush_thread = threading.Thread(target=self.__flush_periodically, daemon=True) 
            self.flush_thread.start() 

    def __flush_periodically(self): 
        # Background thread method to flush metrics every 1 minute 
        while True: 
            time.sleep(60) 
            self.__1_min_flush()
            #to-do need to handle thread termination, as it might hang exit in waiting state

    def __flush_mem_metrics_to_disk(self):
        # Use a temporary list to store the current metrics 
        temp_metrics = self.mem_metrics[:] 
        self.mem_metrics = [] 
        
        with open(self.metrics_file, 'a') as file: 
            for metric in temp_metrics: 
                file.write(f"{self.perf_influxdb},{self.__get_influxdb_time()},{metric.test_type},{metric.file_size},{metric.execution},{metric.crc},{metric.cost},{metric.cli_err},{metric.nw_err},{metric.un_err}\n")
    
    def __1_min_flush(self): 
        # Every 1 minute, calculate stats and flush metrics to disk 
        self.__calculate_stats() 
        self.__flush_mem_metrics_to_disk()

    def shutdown(self): 
        # Shutdown the Performance instance 
        self.__flush_mem_metrics_to_disk() 
        self._instance = None

    def __get_influxdb_time(self):
        # Get current UTC time with nanoseconds 
        current_time = datetime.datetime.utcnow() 
        
        # Format the time for InfluxDB with nanosecond precision 
        formatted_time = current_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3] + 'Z'

        return(formatted_time)
    
    def __calculate_stats(self):
        # Calculate statistics for all metrics in mem_metrics 
        stats = defaultdict(lambda: {'count': 0, 'min': float('inf'), 'max': float('-inf'), 'total_time': 0}) 
        
        for metric in self.mem_metrics: 
            name, time = metric.test_type, metric.execution 
            stats[name]['count'] += 1 
            stats[name]['min'] = min(stats[name]['min'], time) 
            stats[name]['max'] = max(stats[name]['max'], time) 
            stats[name]['total_time'] += time 
        
        with open(self.metrics_summary_file, 'a') as file: 
            for name, data in stats.items(): 
                mean_time = round( data['total_time'] / data['count'], 2) 
                file.write(f"{self.perf_influxdb_summary},{self.__get_influxdb_time()},{name},{data['count']},{data['min']},{data['max']},{mean_time}\n")

    def add_metric(self, results: 'Performance.TestResults' ):
        log_writer.log(f"+ + {self.__class__.__name__}/{inspect.currentframe().f_code.co_name}: Add Metric -> {results.test_type},{results.execution:.2f}s", logging.INFO) 
        self.mem_metrics.append(results)

    class TestResults: 
        def __init__( 
                self, 
                test_type: str, 
                file_size: Optional[float] = None, 
                execution: Optional[float] = None, 
                crc: Optional[float] = None, 
                cost: Optional[float] = None, 
                cli_err: int = 0, 
                nw_err: int = 0, 
                un_err: int = 0 
        ): 
            self.test_type = test_type 
            self.file_size = file_size 
            self.execution = execution 
            self.crc = crc 
            self.cost = cost 
            self.cli_err = cli_err 
            self.nw_err = nw_err 
            self.un_err = un_err 
        
        def __repr__(self): 
            return ( 
                f"TestResults(test_type={self.test_type!r}, file_size={self.file_size!r}, execution={self.execution!r}, " 
                f"crc={self.crc!r}, cost={self.cost!r}, cli_err={self.cli_err!r}, nw_err={self.nw_err!r}, un_err={self.un_err!r})" 
            )

    class Test: 
        def __init__(self, test_type): 
            self.test_type = test_type 
            self.execution_time = 0
            self.start_time = None
            self.performance = Performance() # Get the singleton instance of Performance 

        def start_timer(self):
            self.start_time = time.time()

        def stop_timer(self):
            if self.start_time is not None: 
                self.execution_time = time.time() - self.start_time #native in seconds, might need over-ride to prevent any interpriter sillyness
                self.start_time = None   

        def add_results(self, results: 'Performance.TestResults' ):
            results.test_type = self.test_type
            results.execution = round(self.execution_time, 2) #todo - limit to 2 decimals
            self.performance.add_metric(results) 
            del self

log_writer = LogWriter(log_to_file=True)