from multiprocessing import Queue

import logging

class MyHandler(object):
    def handle(self, record):
        #print(record)
        logging.getLogger(record.name).handle(record)

logQueue = Queue()

worker_config = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'queue': {
            'class': 'logging.handlers.QueueHandler',
            'queue': logQueue
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
    #'respect_handler_level': True,
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
            'level': 'DEBUG',
            'formatter': 'brief'
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'test.log',
            'mode': 'w',
            'formatter': 'detailed',
            'level': 'DEBUG'
        },
        'queue': {
            'class': 'logging.handlers.QueueHandler',
            'queue': logQueue
        },
    },
    #'root': {
    #    'handlers': ['file']
    #},
    'loggers': {
        'project': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
        'listener': {
            'handlers': ['queue'],
            'level': 'DEBUG',
        },
        'project.TP2': {
            'level': 'INFO',
        }
    }
}
