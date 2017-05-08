import logging, logging.handlers , _thread

from multiprocessing import Queue, Event, Process
#from threading import Thread
from time import sleep

def logListener(queue):
    root = logging.getLogger()
    root.addHandler(logging.FileHandler('test.log'))
    #root.addHandler(logging.StreamHandler())
    while True:
        try:
            record = queue.get()
            if record is None:
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            import sys, traceback
            print >> stderr, 'Error in logging process!'
            traceback.print_exc(file=sys.stderr)

class QueueHandler(logging.Handler):
    """
    This is a logging handler which sends events to a multiprocessing queue.

    The plan is to add it to Python 3.2, but this can be copy pasted into
    user code for use with earlier Python versions.
    """

    def __init__(self, queue):
        """
        Initialise an instance, using the passed queue.
        """
        logging.Handler.__init__(self)
        self.queue = queue

    def emit(self, record):
        """
        Emit a record.
        Writes the LogRecord to the queue.
        """
        try:
            ei = record.exc_info
            if ei:
                dummy = self.format(record) # just to get traceback text into record.exc_text
                record.exc_info = None  # not needed any more
            self.queue.put_nowait(record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


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


    logger = logging.getLogger('root')
    logger.handlers = []

    logQueue = Queue()

    logger.addHandler(logging.StreamHandler()) # screen output for testing
    handler = QueueHandler(logQueue)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)



    #_thread.start_new_thread(logListener,(logQueue,))    # <---- Enabling this thread seems to cause the issue



    proc_count = 1

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
