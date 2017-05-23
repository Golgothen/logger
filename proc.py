from multiprocessing import Process, Queue, Event
import logging, logging.config #, logging.handlers
import _thread
from time import sleep

from general import *

class TestProc(Process):
    def __init__(self, **kwargs):
        super(TestProc, self).__init__()
        self.__pipe = None
        for k in kwargs:
            if k == 'NAME':
                self.name = kwargs[k]
            if k == 'STOP':
                self.__stop_event = kwargs[k]
            if k == 'RESUME':
                self.__resume_event = kwargs[k]
            if k == 'PAUSE':
                self.__pause_event = kwargs[k]
            if k == 'CONFIG':
                self.__config = kwargs[k]

        self.running = False
        self.paused = False

    def run(self):
        logging.config.dictConfig(worker_config)      # Load worker_config from general.py
        logname = self.name.split(' ')
        logname = logname[0][:1] + logname[1][:1] + logname[2][:1]
        logger = logging.getLogger(logname)         # create a logger with the process name as the logger name
        print('{}, {}'.format(logger, logger.name ))
        _thread.start_new_thread(self.stop,())
        _thread.start_new_thread(self.pause,())
        _thread.start_new_thread(self.resume,())
        self.running = True
        logger.info('Process {} started'.format(self.name))

        while self.running:
            while self.running and not self.paused:
                logger.debug('Sample message from process {} on PID {}'.format(self.name, self.pid))
                sleep(1)
            logger.info('Process {} paused'.format(self.name))
            sleep(0.5)
        logger.info('Process {} exiting'.format(self.name))

    def stop(self):
        self.__stop_event.wait()
        self.running = False
        # No need to restart this thread as the process will be exiting anyway

    def pause(self):
        self.__pause_event.wait()
        self.paused = True
        self.__pause_event.clear()
        _thread.start_new_thread(self.pause,())

    def resume(self):
        self.__resume_event.wait()
        self.paused = False
        self.__resume_event.clear()
        _thread.start_new_thread(self.resume,())

