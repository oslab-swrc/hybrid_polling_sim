# SPDX-FileCopyrightText: Copyright (c) 2021 Kookmin University
# SPDX-License-Identifier: MIT

from simulator import Simulator


sleep_ratios = [i for i in range(5, 105, 5)]
update_periods = [1, 5, 10, 100, 1000] + [i for i in range(20, 100, 10)] + [i for i in range(200, 1000, 100)]
sim = Simulator(log_folder="scenario3", sleep_ratios=sleep_ratios, update_periods=update_periods)

sim.run()