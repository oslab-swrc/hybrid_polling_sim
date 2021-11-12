# SPDX-FileCopyrightText: Copyright (c) 2021 Kookmin University
# SPDX-License-Identifier: MIT

import sys
import math
from multiprocessing import Pool

class Simulator:
    def __init__(self, core_list=[0], 
                        log_folder="./scenario1", 
                        sleep_percentages=[i for i in range(10, 100, 10)],
                        update_intervals=[1, 10, 100, 1000],
                        overslept_threshold=0.05,
                        multi_thread=True):
        self.core_list = core_list
        self.log_folder = log_folder
        self.log_data = []
        self.sleep_percentages = sleep_percentages
        self.update_intervals = update_intervals
        self.overslept_threshold = overslept_threshold
        self.multi_thread = multi_thread
        
    def get_data_from_log(self):
        for core in self.core_list:
            temp_file_path = f"{self.log_folder}/simulator_log_{core}.csv"
            try:
                f = open(temp_file_path)
                log_data = f.readlines()
                f.close()
            except FileNotFoundError:
                print(f"File Not found: {temp_file_path}")
                sys.exit()
            
            log_header, io_data = log_data[0], log_data[1:]
            for i in range(len(io_data)):
                io_data[i] = list(map(int, io_data[i].split(',')))
                
            self.log_data += io_data

        self.log_data.sort(key=lambda x: x[1])

    def calc_efficiency(self, algorithm, sleep_percentage, update_interval_in_ms):
        # algorithm == 0 -> mean / algorithm == 1 -> min
        current_sleep_time_in_ns = 0
        latest_update_time = 0
        
        total_io_count = 0
        total_miss_count = 0
        total_io_time_in_ns = 0
        total_polling_time_in_ns = 0

        io_time_min = 9999999999
        io_time_sum = 0
        io_count = 0

        total_underslept_time = 0
        total_overslept_time = 0
        total_trace_time = 0

        for io_time, timestamp in self.log_data:
            # get miss result (if io_time smaller than sleep_time -> miss)
            if io_time < current_sleep_time_in_ns:
                total_miss_count += 1

            # get total io count
            total_io_count += 1

            # get total overslept time
            total_overslept_time += max(0, current_sleep_time_in_ns - io_time)

            # get total underslept_time
            total_underslept_time += max(0, io_time - current_sleep_time_in_ns)

            # get total io_time
            total_io_time_in_ns += max(io_time, current_sleep_time_in_ns)
            total_trace_time += io_time
            
            # calculate polling_time
            total_polling_time_in_ns += max(0, io_time - current_sleep_time_in_ns)

            # if current sleep time greater than io_time -> io_time is sleep_time
            # mean
            if algorithm == 0:
                io_time_sum += max(io_time, current_sleep_time_in_ns)
                io_count += 1
            # min
            else:
                if max(io_time, current_sleep_time_in_ns) < io_time_min:
                    io_time_min = max(io_time, current_sleep_time_in_ns)
            
            # update interval check
            if total_io_time_in_ns - latest_update_time > update_interval_in_ms * 1000000:
                # print((total_io_time_in_ns - latest_update_time) / 1000000)
                # mean
                if algorithm == 0:
                    current_sleep_time_in_ns = io_time_sum / io_count
                    current_sleep_time_in_ns *= sleep_percentage
                    current_sleep_time_in_ns /= 100
                    current_sleep_time_in_ns = math.ceil(current_sleep_time_in_ns)
                # min
                else:
                    current_sleep_time_in_ns = math.ceil(io_time_min * sleep_percentage / 100)
                
                # update latest_update_time for next update
                latest_update_time = total_io_time_in_ns

                # reset values
                io_time_min = 9999999999
                io_time_sum = 0
                io_count = 0

        io_time_in_ms = total_io_time_in_ns / 1000000
        polling_time_in_ms = total_polling_time_in_ns / 1000000
        miss_rate = round(total_miss_count / total_io_count * 100, 2)
        cpu_usage = round(total_polling_time_in_ns / total_io_time_in_ns * 100, 2)
        normalized_underslept = round(total_underslept_time / total_trace_time * 100, 2)
        normalized_overslept = round(total_overslept_time / total_trace_time * 100, 2)

        # print(f"Total I/O Time in ms: {io_time_in_ms}")
        # print(f"Total Polling Time in ms: {polling_time_in_ms}")
        # print(f"Miss Rate: {miss_rate}%")
        # print(f"Estimated CPU Usage: {cpu_usage}%")
        # print(f"Normalized Underslept: {normalized_underslept}%")
        # print(f"Normalized Overslept: {normalized_overslept}%")

        return {"config": [algorithm, sleep_percentage, update_interval_in_ms],
                "io_time": io_time_in_ms, 
                "polling_time": polling_time_in_ms, 
                "miss_rate": miss_rate, 
                "cpu_usage": cpu_usage, 
                "normalized_underslept": normalized_underslept, 
                "normalized_overslept": normalized_overslept}

    def run(self):
        self.get_data_from_log()
        test_params = []
        # algorithm: 0 -> mean, 1 -> min
        algorithm_list = [0, 1]
        for algorithm in algorithm_list:
            for sleep_percentage in self.sleep_percentages:
                for interval in self.update_intervals:
                    # print(algorithm, sleep_percentage, interval)
                    test_params.append((algorithm, sleep_percentage, interval))
        

        # multi thread
        if self.multi_thread:
            p = Pool()
            all_result = p.starmap(self.calc_efficiency, test_params)
        # single thread
        else:
            all_result = []
            for params in test_params:
                result = self.calc_efficiency(params[0], params[1], params[2])
                all_result.append(result)

        best_config = None
        best_cpu_usage = 100
        best_result = None
        default_result = None

        for result in all_result:
            if result["normalized_overslept"] <= self.overslept_threshold and result["cpu_usage"] < best_cpu_usage:
                best_cpu_usage = result["cpu_usage"]
                best_config = result["config"]
                best_result = result
            
            if result["config"] == [0, 50, 100]:
                default_result = result

        if best_config is not None:
            print("Best Config")
            print(f"Algorithm: {'mean' if best_config[0] == 0 else 'min'}")
            print(f"Sleep Percentage: {best_config[1]}%")
            print(f"Update Interval: {best_config[2]}ms")
            print("\nExtra Information")
            print(f"Estimated I/O Time: {best_result['io_time']}ms")
            print(f"Estimated Polling Time: {best_result['polling_time']}ms")
            print(f"Estimated Miss Rate: {best_result['miss_rate']}%")
            print(f"Estimated CPU Usage: {best_result['cpu_usage']}%")
            print(f"Default Estimated I/O Time: {default_result['io_time']}ms")
            print(f"Default Estimated Polling Time: {default_result['polling_time']}ms")
            print(f"Default Estimated Miss Rate: {default_result['miss_rate']}%")
            print(f"Default Estimated CPU Usage: {default_result['cpu_usage']}%")
        else:
            print("Optimal Config Not Found")