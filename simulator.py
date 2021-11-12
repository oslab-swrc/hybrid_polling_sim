# SPDX-FileCopyrightText: Copyright (c) 2021 Kookmin University
# SPDX-License-Identifier: MIT

import sys
import math
from multiprocessing import Pool

class Simulator:
    def __init__(self, core_list=[0], 
                        log_folder="./scenario1", 
                        sleep_ratios=[i for i in range(10, 100, 10)],
                        update_periods=[1, 10, 100, 1000],
                        overslept_threshold=0.05,
                        multi_thread=True):
        self.core_list = core_list
        self.log_folder = log_folder
        self.log_data = []
        self.sleep_ratios = sleep_ratios
        self.update_periods = update_periods
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

    def calc_efficiency(self, mode, sleep_ratio, update_period_in_ms):
        # mode == 0 -> mean / mode == 1 -> min
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
            if mode == 0:
                io_time_sum += max(io_time, current_sleep_time_in_ns)
                io_count += 1
            # min
            else:
                if max(io_time, current_sleep_time_in_ns) < io_time_min:
                    io_time_min = max(io_time, current_sleep_time_in_ns)
            
            # update period check
            if total_io_time_in_ns - latest_update_time > update_period_in_ms * 1000000:
                # print((total_io_time_in_ns - latest_update_time) / 1000000)
                # mean
                if mode == 0:
                    current_sleep_time_in_ns = io_time_sum / io_count
                    current_sleep_time_in_ns *= sleep_ratio
                    current_sleep_time_in_ns /= 100
                    current_sleep_time_in_ns = math.ceil(current_sleep_time_in_ns)
                # min
                else:
                    current_sleep_time_in_ns = math.ceil(io_time_min * sleep_ratio / 100)
                
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

        return {"config": [mode, sleep_ratio, update_period_in_ms],
                "io_time": io_time_in_ms, 
                "polling_time": polling_time_in_ms, 
                "miss_rate": miss_rate, 
                "cpu_usage": cpu_usage, 
                "normalized_underslept": normalized_underslept, 
                "normalized_overslept": normalized_overslept}

    def run(self):
        self.get_data_from_log()
        test_params = []
        # mode: 0 -> mean, 1 -> min
        mode_list = [0, 1]
        for mode in mode_list:
            for sleep_ratio in self.sleep_ratios:
                for period in self.update_periods:
                    # print(mode, sleep_ratio, period)
                    test_params.append((mode, sleep_ratio, period))
        

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
            print(f"Mode: {'mean' if best_config[0] == 0 else 'min'}")
            print(f"Sleep Percentage: {best_config[1]}%")
            print(f"Update period: {best_config[2]}ms")
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