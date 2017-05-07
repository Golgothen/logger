import logging, logging.handlers, logging.config, os

from multiprocessing import Process, Queue, Pipe, Event
from threading import Thread

#from pipewatcher import PipeWatcher

from time import sleep

logger = logging.getLogger('root')

class LogListener(Process):

    def __init__(self, log_queue, stop_event):
        super(LogListener, self).__init__()
        self.logQueue = q
        self.stop_event = stop_event

    def run(self):

        logger_config = {
            'version': 1,
            'disable_existing_loggers': True,
            'formatters': {
                'detailed': {
                    'class': 'logging.Formatter',
                    'format': '%(asctime)-16s:%(levelname)-8s[%(module)-12s.%(funcName)-20s:%(lineno)-5s] %(message)s'
                },
                'brief': {
                    'class': 'logging.Formatter',
                    'format': '%(message)s'
                }
            },
            'handlers': {
                'colsole': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter' : 'brief',
                },
                'file' : {
                    'class': 'logging.FileHandler',
                    'filename': 'debug.log',
                    'mode': 'w',
                    'formatter': 'detailed',
                    'level': 'DEBUG',
                },
            'loggers': {
                'root': {
                    'handlers': ['console', 'file']
                },
            }

        logging.config.dictConfig(logger_config)
        listener = logging.handlers.QueueListener(self.logQueue)
        listener.start()
        logger = logging.getLogger('root')
        stop_even.wait()
        listener.stop()


class TestProc(Process):
    def __init__(self, comms, name):
        super(TestProc, self).__init__()
        self.name = name
        self.__pipe = PipeWatcher(self, comms, self.name)
        self.running = False

    def run(self):
        self.__pid = os.getpid()
        self.running = True
        while self.running:
            logger.info('Sample message from process {}'.format(self.__pid))
            sleep(1)
        logger.info('Process {} exiting'.format(self.pid))

    def stop(self, p):
        self.running = False

class PipeWatcher(Thread):

    def __init__(self, parent, pipe, name):
        super(PipeWatcher, self).__init__()
        self.__pipe = pipe
        self.__parent = parent
        self.__running = False
        self.name = name
        self.daemon = True

    def run(self):
        self.__running = True
        logger.info('Starting listener thread {}'.format(self.name))
        try:
            while self.__running:
                while self.__pipe.poll(None):  # Block indefinately waiting for a message
                    m = self.__pipe.recv()
                    logger.info('{} {} with {}'.format(self.name, m.message, m.params))
                    response = getattr(self.__parent, m.message.lower())(m.params)
                    if response is not None:
                        logger.debug('{} response.'.format(response.message))
                        self.send(response)
        except (KeyboardInterrupt, SystemExit):
            self.__running = False
        except:
            logger.critical('Unhandled exception occured in PipeWatcher thread {}: {}'.format(self.name, sys.exc_info))

    # Public method to allow the parent to send messages to the pipe
    def send(self, msg):
        self.__pipe.send(msg)

class Message():
    def __init__(self, message, **kwargs):
        self.message = message
        self.params = dict()
        for k in kwargs:
            self.params[k] = kwargs[k]
        logger.debug('Message: {} : {}'.format(self.message, self.params))

if __name__ == '__main__':
    q = Queue()
    e = Event()
    log = LogListener(q, e)
    log.start()

    logger_config = {
        'version': 1,
        'disable-existing_loggers': True,
        'handlers': {
            'queue': {
                'class': 'logging.handlers.QueueHandler',
                'queue': q,
            },
        },
        'root' : {
            'level': 'DEBUG',
            'handlers': ['queue']
        },
    }

    logging.config.dictConfig(logger_config)
    logger = logging.getLogger('root')

    procs = []
    for a in range(5):
        snd, rcv = Pipe()
        wp = {}
        wp['PROCESS'] = TestProc(snd, 'Test Process {}'.format(a))
        wp['PIPE'] = rcv
        procs.append(wp)
        sleep(0.1)
        wp['PROCESS'].start()

    sleep(10)
    for p in procs:
        procs[p]['PIPE'].send(Message('STOP'))
        procs[p]['PROCESS'].join()
    e.set()
    log.join()
