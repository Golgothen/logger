import logging, logging.handlers, logging.config, os

from multiprocessing import Process, Queue, Pipe
from threading import Thread

#from pipewatcher import PipeWatcher

from time import sleep


class TestProc(Process):
    def __init__(self, comms, name, q, config):
        super(TestProc, self).__init__()
        self.name = name
        self.__pipe = PipeWatcher(self, comms, self.name, q, config)
        self.running = False
        self.logger = lgging.config.dictConfig(config)

    def run(self):
        self.__pid = os.getpid()
        self.running = True
        while self.running:
            self.logger.info('Sample message from process {}'.format(self.__pid))
            sleep(1)
        self.logger.info('Process {} exiting'.format(self.pid))

    def stop(self, p):
        self.running = False

class PipeWatcher(Thread):

    def __init__(self, parent, pipe, name, q, config):
        super(PipeWatcher, self).__init__()
        self.__pipe = pipe
        self.__parent = parent
        self.__running = False
        self.name = name
        self.daemon = True
        self.logger = self.logging.config.dictConfig(config)

    def run(self):
        self.__running = True
        self.logger.info('Starting listener thread {}'.format(self.name))
        try:
            while self.__running:
                while self.__pipe.poll(None):  # Block indefinately waiting for a message
                    m = self.__pipe.recv()
                    self.logger.info('{} {} with {}'.format(self.name, m.message, m.params))
                    response = getattr(self.__parent, m.message.lower())(m.params)
                    if response is not None:
                        self.logger.debug('{} response.'.format(response.message))
                        self.send(response)
        except (KeyboardInterrupt, SystemExit):
            self.__running = False
        except:
            self.logger.critical('Unhandled exception occured in PipeWatcher thread {}: {}'.format(self.name, sys.exc_info))

    # Public method to allow the parent to send messages to the pipe
    def send(self, msg):
        self.__pipe.send(msg)

class Message():
    def __init__(self, message, **kwargs):
        self.message = message
        self.params = dict()
        for k in kwargs:
            self.params[k] = kwargs[k]
        #logger.debug('Message: {} : {}'.format(self.message, self.params))

if __name__ == '__main__':
    q = Queue()

    worker_config = {'version': 1,
                     'disable_existing_loggers': True,
                     'handlers':
                        {'queue':
                            {'class': 'logging.handlers.QueueHandler',
                             'queue': q,
                            },
                        },
                     'root':
                         {'level': 'DEBUG',
                          'handlers': ['queue']
                         },
                    }



    logger = logging.getLogger('root')

    #logName = (datetime.now().strftime('RUN%Y%m%d')+'.log')
    handler = logging.StreamHandler() # sends output to stderr
    #file_handler = logging.FileHandler('./'+logName) # sends output to file
    handler.setFormatter(logging.Formatter('%(asctime)-16s:%(levelname)-8s[%(module)-12s.%(funcName)-20s:%(lineno)-5s] %(message)s'))
    listener = logging.handlers.QueueListener(q)
    listener.start()

    procs = []
    for a in range(5):
        snd, rcv = Pipe()
        procs[a] = {'PROCESS' : TestProc(rcv, 'Test Process {}'.format(a), q, worker_config), 'PIPE' : snd }
        sleep(0.1)
        procs[a]['PROCESS'].start()

    sleep(10)
    for p in procs:
        procs[p]['PIPE'].send(Message('STOP'))

