from multiprocessing import Process, Queue, Event
from time import sleep
from proc import TestProc

#from queuehandler import LogListener, QueueHandler
import _thread

#import logging, logging.handlers, logging.config

from general import *

lp = LogListener(log_config)
lp.start()


if __name__ == '__main__':

    logging.config.dictConfig(worker_config)
    logger = logging.getLogger()

    logger.info('Logging initialised')
    logger.info('Listener started')

    proc_count = 10

    procs = []
    for a in range(proc_count):
        stop_event = Event()
        pause_event = Event()
        resume_event = Event()
        wp = {}
        wp['PROCESS'] = TestProc(NAME = 'Test Process {}'.format(a),
                                 STOP = stop_event,
                                 PAUSE = pause_event,
                                 RESUME = resume_event)
                                 #CONFIG = worker_config)
        wp['STOP'] = stop_event
        wp['PAUSE'] = pause_event
        wp['RESUME'] = resume_event
        procs.append(wp)
        wp['PROCESS'].start()
        sleep(0.01)

    sleep(2)
    logger.info('Pausing processes')
    for a in range(proc_count):
        procs[a]['PAUSE'].set()

    sleep(2)
    logger.info('Resuming processes')
    for a in range(proc_count):
        procs[a]['RESUME'].set()

    sleep(2)
    logger.info('Stopping processes')
    for a in range(proc_count):
        procs[a]['STOP'].set()
    for a in range(proc_count):
        procs[a]['PROCESS'].join()

    lp.stop()
    lp.join()
