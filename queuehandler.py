from multiprocessing import Queue, Process
import logging, logging.handlers


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

#class LogListener(Process):
#    def __init__(self, queue):
#        super(LogListener, self).__init__()
#        self.__queue = queue

def logListener():
    root = logging.getLogger()
    root.handlers = []
    #root.addHandler(logging.FileHandler('test.log'))
    root.addHandler(logging.StreamHandler())
    while True:
        try:
            record = self.__queue.get()
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

