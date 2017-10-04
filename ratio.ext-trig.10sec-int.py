#!/bin/bash

# For now, this script will load a pre-generated state file (*.sta) which is stored locally on the counter
# In the future, this script will include UI elements to allow changes to measurement states

import sys
import visa
import time
import logging
from logging.handlers import TimedRotatingFileHandler as TRFH
import os
from datetime import datetime


def main():
    print_header()

    script_dir = os.getcwd()
    instrument_IP = "TCPIP0::192.168.23.5::inst0::INSTR"
    state_file = "INT:\\RAT.EXTRIG.10sec.sta"

    inst = inst_connect(instrument_IP)
    inst_id = inst.query('*IDN?')
    print(inst_id)

    inst_load_state(inst, state_file)  # read local-to-inst state file and prepare instrument to take measurement

    inst_data_start(inst)    # start measurement and store data in instrument buffer

    log_file = log_file_setup(script_dir) # create log file with header

    logger = time_rotating_log_setup(log_file) # create a logger instance

    data_logging(logger, inst)   # automatically start logging data and writing to file, abort on user input

    inst_disconnect(inst)    # abort measurement routine and disconnect from the instrument


def print_header():
    print("---------------------------------")
    print("   Keysight 53220A Data Logger")
    print("   " + str(datetime.utcnow()))
    print("---------------------------------")


def inst_connect(inst_IP):
    try:
        rm = visa.ResourceManager()
        inst = rm.open_resource(inst_IP)
        return inst

    except:
        raise Exception("ERROR: Cannot connect to instrument IP: {}".format(inst_IP[8:-14]))
        # print(e.message)
        sys.exit(0)


def inst_load_state(inst, sta):
    inst.write('*CLS')
    time.sleep(1)
    inst.write('*RST')
    time.sleep(1)
    inst.write(':MMEMory:LOAD:STATe "%s"' % sta)


def inst_data_start(inst):
    inst.write(':INITiate:IMMediate')


def log_file_setup(path):

    log_file_path = os.path.join(path, "logs")
    if not os.path.exists(log_file_path):
        os.mkdir(log_file_path)

    # time_stamp = time.strftime("%Y%m%d")
    ind = 1
    # log_file = os.path.join(log_file_path, "counterLog.{}.{:03d}.csv".format(time_stamp, ind))
    log_file = os.path.join(log_file_path, "counterLog.{:03d}.csv".format(ind))

    while os.path.exists(log_file):
        ind += 1
    #     log_file = os.path.join(log_file_path, "counterLog.{}.{:03d}.csv".format(time_stamp, ind))
        log_file = os.path.join(log_file_path, "counterLog.{:03d}.csv".format(ind))

    with open(log_file, "w") as log:
        log.write("Time, CounterData\n")

    return log_file


def time_rotating_log_setup(log_file):
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # when: s=sec, m=min, h=hour, d=day, W0-W7=weekday (0=monday), midnight=midnight
    handler = TRFH(log_file, when='midnight', interval=1, backupCount=0, encoding='utf8', utc=True)
    logger.addHandler(handler)

    return logger


def data_logging(logger, inst):
    # print("Log file path: " + os.path.abspath(log_file))
    print("Logging initiated..")

    inst.write(':FORMat:DATA %s' % ('ASC'))

    while True:
        time.sleep(1)
        measurement_block = inst.query_binary_values(':R? %d' % (1), 's', False)
        meas = str(measurement_block)[3:-2]

        if meas != "":
            print(meas)
            # with open(log_file, 'a') as log:
            #     log.write(str(datetime.utcnow()) + "," + meas + "\n")
            logger.info(str(datetime.utcnow()) + ',' + meas)


def inst_disconnect(inst):
    inst.close()
    visa.ResourceManager().close()


if __name__ == '__main__':
    main()
