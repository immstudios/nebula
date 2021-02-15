__all__ = ["messaging"]

import time
import json
import socket

from nxtools import log_traceback
from nebulacore import config


class Messaging():
    def __init__(self):
        self.configured = False

    def configure(self):
        self.addr = config.get("seismic_addr", "224.168.2.8")
        self.port = int(config.get("seismic_port", 42112))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        self.configured = True

    def send(self, method, **data):
        if not self.configured:
            return
        try:
            self.sock.sendto(
                bytes(
                    json.dumps([
                        time.time(),
                        config["site_name"],
                        config["host"],
                        method,
                        data
                    ]),
                    "utf-8"
                ),
                (self.addr, self.port)
            )
        except Exception:
            log_traceback(handlers=False)

    def __del__(self):
        if self.configured:
            self.sock.close()

messaging = Messaging()
