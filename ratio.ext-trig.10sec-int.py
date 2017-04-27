#!/bin/bash

# For now, this script will load a pre-generated state file (*.sta) which is stored locally on the counter
# In the future, this script will include UI elements to allow changes to measurement states

import visa
import time
import logging
from logging.handlers import TimedRotatingFileHandler as TRFH
import os
from datetime import datetime
from subprocess import call


def main():
    printHeader()

    scriptDir = os.getcwd()
    instrumentIP = "TCPIP0::192.168.23.5::inst0::INSTR"
    stateFile = "INT:\\RAT.EXTRIG.10sec.sta"

    inst = instConnect(instrumentIP)
    instID = inst.query('*IDN?')
    print(instID)

    instLoadState(inst, stateFile)  # read local-to-inst state file and prepare instrument to take measurement

    instDataStart(inst)    # start measurement and store data in instrument buffer

    logFile = logFileSetup(scriptDir) # create log file with header

    logger = timeRotatingLogSetup(logFile) # create a logger instance

    dataLogging(logger, inst)   # automatically start logging data and writing to file, abort on user input

    instDisconnect(inst)    # abort measurement routine and disconnect from the instrument


def printHeader():
    print("---------------------------------")
    print("   Keysight 53220A Data Logger")
    print("   " + str(datetime.utcnow()))
    print("---------------------------------")


def instConnect(instIP):
    rm = visa.ResourceManager()
    inst = rm.open_resource(instIP)

    return inst


def instLoadState(inst, sta):
    inst.write('*CLS')
    time.sleep(1)
    inst.write('*RST')
    time.sleep(1)
    inst.write(':MMEMory:LOAD:STATe "%s"' % sta)


def instDataStart(inst):
    inst.write(':INITiate:IMMediate')


def logFileSetup(path):

    logFilePath = os.path.join(path, "logs")
    if not os.path.exists(logFilePath):
        os.mkdir(logFilePath)

    timeStamp = time.strftime("%Y%m%d")
    ind = 1
    # logFile = os.path.join(logFilePath, "counterLog.{}.{:03d}.csv".format(timeStamp, ind))
    logFile = os.path.join(logFilePath, "counterLog.{:03d}.csv".format(ind))

    while os.path.exists(logFile):
        ind += 1
    #     logFile = os.path.join(logFilePath, "counterLog.{}.{:03d}.csv".format(timeStamp, ind))
        logFile = os.path.join(logFilePath, "counterLog.{:03d}.csv".format(ind))

    with open(logFile, "w") as log:
        log.write("Time, CounterData\n")

    return logFile


def timeRotatingLogSetup(logFile):
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # when: s=sec, m=min, h=hour, d=day, W0-W7=weekday (0=monday), midnight=midnight
    handler = TRFH(logFile, when='midnight', interval=1, backupCount=0, encoding='utf8', utc=True)
    logger.addHandler(handler)

    return logger


def dataLogging(logger, inst):
    # print("Log file path: " + os.path.abspath(logFile))
    print("Logging initiated..")

    inst.write(':FORMat:DATA %s' % ('ASC'))

    while True:
        time.sleep(1)
        measurementBlock = inst.query_binary_values(':R? %d' % (1), 's', False)
        meas = str(measurementBlock)[3:-2]

        if meas != "":
            print(meas)
            # with open(logFile, 'a') as log:
            #     log.write(str(datetime.utcnow()) + "," + meas + "\n")
            logger.info(str(datetime.utcnow()) + ',' + meas)


def instDisconnect(inst):
    inst.close()
    visa.ResourceManager().close()


if __name__ == '__main__':
    main()
