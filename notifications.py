import json
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from os import path

import apprise

TIME_FORMAT = "%Y-%m-%d @ %H:%M:%S"


APPRISE_CONFIG_PATH = "apprise_config.json"

class NotificationHandler:
    def __init__(self):
        self.apb = apprise.Apprise()

        if path.exists(APPRISE_CONFIG_PATH):
            with open(APPRISE_CONFIG_PATH) as json_file:
                configs = json.load(json_file)
                for config in configs:
                    self.apb.add(config["url"])
            self.queue = queue.Queue()
            self.start_worker()
            self.enabled = True
        else:
            self.enabled = False


    def send_notification(self, message, screenshot=False, **kwargs):
        if self.enabled:
            self.queue.put((message, screenshot))

    def message_sender(self):
        while True:
            message, screenshot = self.queue.get()
            if screenshot:
                self.apb.notify(body=message, attach="screenshot.png")
            else:
                self.apb.notify(body=message)
            self.queue.task_done()

    def start_worker(self):
        threading.Thread(target=self.message_sender, daemon=True).start()
