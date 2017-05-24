from multiprocessing import Process, Queue, Event, current_process

import logging

logQueue = Queue()

class MyHandler(object):
    def handle(self, record):
        #print(record.name)
        logger = logging.getLogger(record.name)
        record.processName = '%s (for %s)' % (current_process().name, record.processName)
        logger.handle(record)

class LogListener(Process):
    def __init__(self, config):
        super(LogListener, self).__init__()
        self.stop_event = Event()
        self.config = config
        self.name = 'listener'

    def run(self):
        logging.config.dictConfig(self.config)
        listener = logging.handlers.QueueListener(logQueue, MyHandler())
        listener.start()
        self.stop_event.wait()
        listener.stop()

    def stop(self):
        self.stop_event.set()

worker_config = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'queue': {
            'class': 'logging.handlers.QueueHandler',
            'queue': logQueue
        },
    },
    'loggers': {
        'TP2': {
            'level': 'INFO',
        },
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['queue']
    },
}

log_config = {
    'version': 1,
    'disable_existing_loggers': True,
    'respect_handler_level': True,
    'formatters': {
        'detailed': {
            'class': 'logging.Formatter',
            'format': '%(processName)-14s:%(name)-3s:%(asctime)-16s:%(levelname)-5s[%(module)-4s.%(funcName)-3s:%(lineno)-2s] %(message)s'
        },
        'brief': {
            'class': 'logging.Formatter',
            'format': '%(levelname)-8s:%(name)-3s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'ERROR',
            'formatter': 'brief'
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'test.log',
            'mode': 'w',
            'formatter': 'detailed',
            'level': 'DEBUG'
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO'
    },
}

