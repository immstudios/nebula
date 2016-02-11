import time
import thread

from .core import *

__all__ = ["BaseAgent"]

class BaseAgent():
    def __init__(self, once=False):
        self.on_init()
        self.is_running = self.should_run = False
        if once:
            self.main()
        else:
            logging.info("Starting", self.__class__.__name__)
            thread.start_new_thread(self.run,())
            self.is_running = self.should_run = True

    def on_init(self):
        pass

    def on_shutdown(self):
        pass

    def shutdown(self):
        self.should_run = False

    def run(self):
        while self.should_run:
            try:
                self.main()
            except:
                log_traceback()
            time.sleep(1)
        self.on_shutdown()
        self.is_running = False

    def main(self):
        pass
