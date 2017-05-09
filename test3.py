from multiprocessing import Event, Process, Queue
from time import sleep
from queuehandler import LogListener, QueueHandler
import logging, _thread


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

        self.running = False
        self.paused = False

    def run(self):
        _thread.start_new_thread(self.stop,())
        _thread.start_new_thread(self.pause,())
        _thread.start_new_thread(self.resume,())
        self.running = True

        while self.running:
            while self.running and not self.paused:
                logger.info('Sample message from process {} on PID {}'.format(self.name, self.pid))
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

if __name__ == '__main__':

    config = {
             'version': 1,
             'disable_existing_loggers': True,
             'formatters': {
                           'detailed': {
                                       'class': 'logging.Formatter',
                                       'format': '%(asctime)-16s:%(levelname)-8s[%(module)-12s.%(funcName)-20s:%(lineno)-5s] %(message)s'
                                       },
                           'brief': {
                                    'class': 'logging.Formatter',
                                    'format': '%(asctime)-16s: %(message)s'
                                    }
                           },
             'handlers': {
                         'console': {
                                    'class': 'logging.StreamHandler',
                                    'level': 'INFO',
                                    'formatter': 'brief'
                                    },
                         'file': {
                                 'class': 'logging.FileHandler',
                                 'filename': 'test.log',
                                 'mode': 'w',
                                 'formatter': 'detailed',
                                 'level': 'DEBUG'
                                 }
                         },
             'loggers': {
                        'root': {
                                'handlers': ['console', 'file']
                                },
                        }
             }


    logQueue = Queue()

    listener = LogListener(logQueue, config)
    listener.start()

    logger = logging.getLogger('root')


    handler = QueueHandler(logQueue)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    proc_count = 10

    procs = []
    for a in range(proc_count):
        stop_event = Event()
        pause_event = Event()
        resume_event = Event()
        wp = {}
        wp['PROCESS'] = TestProc(NAME = 'Test Process {}'.format(a), STOP = stop_event, PAUSE = pause_event, RESUME = resume_event)
        wp['STOP'] = stop_event
        wp['PAUSE'] = pause_event
        wp['RESUME'] = resume_event
        procs.append(wp)
        wp['PROCESS'].start()

    sleep(2)
    for a in range(proc_count):
        procs[a]['PAUSE'].set()

    sleep(2)
    for a in range(proc_count):
        procs[a]['RESUME'].set()

    sleep(2)
    for a in range(proc_count):
        procs[a]['STOP'].set()
    for a in range(proc_count):
        procs[a]['PROCESS'].join()

    logQueue.put(None)

