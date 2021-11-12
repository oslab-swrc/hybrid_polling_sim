# SPDX-FileCopyrightText: Copyright (c) 2021 Kookmin University
# SPDX-License-Identifier: MIT

from simulator import Simulator


sleep_percentages = [i for i in range(5, 105, 5)]
update_intervals = [1, 5, 10, 100, 1000] + [i for i in range(20, 100, 10)] + [i for i in range(200, 1000, 100)]
sim = Simulator(log_folder="scenario1", sleep_percentages=sleep_percentages, update_intervals=update_intervals)

sim.run()