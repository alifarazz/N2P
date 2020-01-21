import asyncio as aio
import threading
import signal


class Worker:
    def __init__(self, loop, ws):
        self.thread = threading.Thread(target=self.linit, args=(loop, ws))
        self.loop = loop
        self.thread.start()
        self.thread.join

    def linit(self, loop, coro):
        cancel_signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
        aio.set_event_loop(loop)
        # try:
        loop.run_until_complete(coro)
        # finally:
            # loop.close()

