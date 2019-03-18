import time
import socket
import json

from .common import *

def log_message(message):
    tstamp = time.strftime("%H:%M:%S")
    user = "{}@{}".format(message.data["user"], message.host)
    ltype = {
            0 : "\033[34mDEBUG    \033[0m",
            1 : "INFO     ",
            2 : "\033[33mWARNING  \033[0m",
            3 : "\033[31mERROR    \033[0m",
            4 : "\033[32mGOOD NEWS\033[0m"
            }[message.data["message_type"]]

    mesg = message.data["message"]
    print (tstamp + " " + ltype + " " + user.ljust(22) + " " + mesg)


class SeismicMessage():
    def __init__(self, packet):
        self.timestamp, self.site_name, self.host, self.method, self.data = packet

    @property
    def json(self):
        return json.dumps([
                self.timestamp,
                self.site_name,
                self.host,
                self.method,
                self.data
            ])



def listen():
        sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM,
                socket.IPPROTO_UDP
            )
        sock.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1
            )
        sock.bind(("0.0.0.0", int(config["seismic_port"])))
        sock.setsockopt(
                socket.IPPROTO_IP,
                socket.IP_MULTICAST_TTL,
                255
            )
        sock.setsockopt(
                socket.IPPROTO_IP,
                socket.IP_ADD_MEMBERSHIP,
                socket.inet_aton(config["seismic_addr"]) + socket.inet_aton("0.0.0.0")
            )
        sock.settimeout(1)

        while True:
            try:
                data, addr = sock.recvfrom(4092)
            except (socket.error):
                continue
            try:
                message = SeismicMessage(json.loads(data.decode()))
            except Exception:
                continue

            if message.site_name != config["site_name"]:
                continue

            if message.method == "log":
                log_message(message)




def l(*args):
   listen()

