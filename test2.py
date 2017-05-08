import logging, logging.handlers, logging.config, os, _thread

from multiprocessing import Process, Queue, Pipe, Event
from threading import Thread

#from pipewatcher import PipeWatcher

from time import sleep

logger = logging.getLogger('root')
logger.handlers = []

handler = logging.StreamHandler()
logger.addHandler(handler)
handler = logging.FileHandler('test.log')
logger.addHandler(handler)

logger.setLevel(logging.DEBUG)

class TestProc(Process):
    def __init__(self, **kwargs):
        super(TestProc, self).__init__()
        self.__pipe = None
        for k in kwargs:
            if k == 'NAME':
                self.name = kwargs[k]
            if k == 'PIPE':
                self.__pipe = PipeWatcher(self, kwargs[k], self.name)
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

        if self.__pipe is not None:
            self.__pipe.start()
        self.__pid = os.getpid()
        self.running = True
        while self.running:
            while self.running and not self.paused:
                logger.info('Sample message from process {} on PID {}'.format(self.name, self.__pid))
                sleep(0.1)
            logger.info('Process {} paused'.format(self.name))
            sleep(0.5)
        logger.info('Process {} exiting'.format(self.name))

    def stop(self, p = None):
        self.__stop_event.wait()
        self.running = False
        self.__stop_event.clear()
        _thread.start_new_thread(self.stop,())

    def pause(self, p = None):
        self.__pause_event.wait()
        self.paused = True
        self.__pause_event.clear()
        _thread.start_new_thread(self.pause,())

    def resume(self, p = None):
        self.__resume_event.wait()
        self.paused = False
        self.__resume_event.clear()
        _thread.start_new_thread(self.resume,())

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

    proc_count = 50

    procs = []
    for a in range(proc_count):
        #snd, rcv = Pipe()
        stop_event = Event()
        pause_event = Event()
        resume_event = Event()
        wp = {}
        wp['PROCESS'] = TestProc(NAME = 'Test Process {}'.format(a), STOP = stop_event, PAUSE = pause_event, RESUME = resume_event)
        #wp['PIPE'] = rcv
        wp['STOP'] = stop_event
        wp['PAUSE'] = pause_event
        wp['RESUME'] = resume_event
        procs.append(wp)
        #sleep(0.1)
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
