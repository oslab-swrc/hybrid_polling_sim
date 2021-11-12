# hybrid_polling_sim

The goal of this project is to build a simulator for hybrid polling to enable configuration space exploration without kernel modification, recompilation, and rebooting the test machine. The simulator provides configuration of (1) mode(mean or min), (2) sleep ratio, (3) update period, and (4) other parameters. It also supports multi-thread simulation of multiple configurations. Once a desirable configuration is found, it can be applied to the Linux kernel for evaluation on a real platform.



## License

MIT License



### Usage

You need to build the kernel first.

#### Build

##### Get Source Code

[Kernel Source](https://github.com/oslab-swrc/blk_explore)

```bash
git clone https://github.com/oslab-swrc/blk_explore && git checkout simulator-log
```



##### Before Build

You may need to set

```
#define CPU_CORES 192
```

in block/blk-mq.c(line 49) to your system's core count.



##### Setup

You need to make config.

```bash
make menuconfig
```

SAVE & EXIT



##### Build Command

```bash
make -j$((`nproc`+1)) && make modules -j$((`nproc`+1)) && make modules_install -j$((`nproc`+1)) INSTALL_MOD_STRIP=1 && make install -j$((`nproc`+1))
```

This command automatically detects the number of cores, and builds with {core count} + 1. Or you can just specify core count to use like make -j8.



#### Get Log from Kernel and Setup for Simulator

##### Make Ramdisk for Logging

```bash
sudo mkdir /media/ramdisk
sudo mount -t tmpfs -o rw,size=2G tmpfs /media/ramdisk
```



##### Start Logging

```bash
echo 1 > /sys/block/nvmexn1/queue/io_poll_logging
```

##### Stop Logging

```bash
echo 0 > /sys/block/nvmexn1/queue/io_poll_logging
```

- Start / Stop Logging require root privileges.

- nvmexn1 -> nvme0n1 / nvme1n1 / nvme2n1 ...

  

You can find logs in /media/ramdisk. Logs are split by the core number.



#### Simulator Configuration

You can configure simulator in run.py:

- core_list

- log_folder

- sleep_ratios

- update_periods

- overslept_threshold

- multi_thread

  

##### core_list

- List of Integer
- Simulator uses per-core-logs in core_list.
- Default: [0]

##### log_folder

- String
- Specify log directory
- Default: ./scenario1

##### sleep_ratios

- List of Integer
- Contains sleep ratio for applying to base sleep duration
- Default: [10, 20, 30, 40, 50, 60, 70, 80, 90]
- Unit: %

##### update_periods

- List of Integer
- Contains update periods for hybrid polling
- Default: [1, 10, 100, 1000]
- Unit: ms

##### overslept_threshold

- Float
- Threshold for overslept
- Default: 0.05
- Unit: %

##### multi_thread

- Bool
- Configuration for multi threaded operation
- It uses multiprocessing.Pool.
- if True: test multiple configurations simultaneously.
- else: test configurations sequentially.



#### Run Simulator

After configure, you can run simulator by

```
python3 run.py
```



### Developer Information

#### Requirements

- python 3.6 or later