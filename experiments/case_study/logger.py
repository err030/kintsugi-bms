

import logging
import time
import subprocess

from datetime import datetime

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncLogger import SyncLogger

# URI to the Crazyflie to connect to
uri = 'usb://0'

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

def get_timestamp():
    timestamp = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
    return timestamp

def run_command(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
    return "", result.returncode

f = open(f"/app/case-study/measurements.txt", "w")

def log_stab_callback(timestamp, data, logconf):
    s = '[%d]: %s\n' % (timestamp, data)
    f.write(s)
    print(s)

def simple_log_async(scf, logconf):
    cf = scf.cf
    cf.log.add_config(logconf)
    logconf.data_received_cb.add_callback(log_stab_callback)
    logconf.start()
    time.sleep(60)
    logconf.stop()

if __name__ == '__main__':
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()
    lg_stab = LogConfig(name='Stabilizer', period_in_ms=10)
    lg_stab.add_variable('stabilizer.yaw', 'float')
    lg_stab.add_variable('hotpatch.patch_go', 'float')
    lg_stab.add_variable('hotpatch.tick_active', 'float')
    lg_stab.add_variable('hotpatch.prev_manager', 'float')
    lg_stab.add_variable('hotpatch.context_switches', 'float')
    lg_stab.add_variable('hotpatch.measure_time', 'float')

    measurement = list()
    run_command("make flash")
    time.sleep(3)
    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
        simple_log_async(scf, lg_stab)
