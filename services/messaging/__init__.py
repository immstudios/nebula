import socket
import thread

from urllib2 import urlopen

from nx import *
from nx.services import BaseService

class Service(BaseService):
    def on_init(self):

        self.site_name = config["site_name"]

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0",int(config["seismic_port"])))
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        status = self.sock.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP,socket.inet_aton(config["seismic_addr"]) + socket.inet_aton("0.0.0.0"));
        self.sock.settimeout(1)

        # Message relay

        try:
            host = self.settings.find("http_host").text
        except:
            host = "localhost"

        try:
            port = int(self.settings.find("http_port").text)
        except:
            port = "80"

        try:
            ssl = int(self.settings.find("use_ssl").text)
        except:
            ssl = 0

        self.url = "{protocol}://{host}:{port}/msg_publish?id={site_name}".format(protocol=["http","https"][ssl], host=host, port=port, site_name=config["site_name"])

        # Logging

        try:
            self.log_path = self.settings.find("log_path").text
        except:
            self.log_path = False

        if self.log_path and not os.path.exists(self.log_path):
            try:
                os.makedirs(self.log_path)
            except:
                self.log_path = False


        thread.start_new_thread(self.listen, ())


    def listen(self):
        while True:
            try:
                message, addr = self.sock.recvfrom(1024)
            except (socket.error):
                continue

            try:
                tstamp, site_name, host, method, data = json.loads(message)
            except:
                logging.warning("Malformed seismic message detected")
                continue

            if site_name == config["site_name"]:
                try:
                    self.send_message("{}\n".format(message.replace("\n","")))
                except:
                    logging.error("Unable to relay {} message to {} ".format(method, self.url))

                if self.log_path and method == "log":
                    try:
                        log = "{}\t{}\t{}@{}\t{}\n".format(
                                time.strftime("%H:%M:%S"),

                                {DEBUG      : "DEBUG    ",
                                INFO       : "INFO     ",
                                WARNING    : "WARNING  ",
                                ERROR      : "ERROR    ",
                                GOOD_NEWS  : "GOOD NEWS"}[data["msg_type"]],


                                data["user"],
                                host,
                                data["message"]
                            )
                    except:
                        pass
                    else:
                        fn = os.path.join(self.log_path, time.strftime("%Y-%m-%d.txt"))
                        f = open(fn, "a")
                        f.write(log)
                        f.close()


    def send_message(self, message):
        post_data = message
        result = urlopen(self.url, post_data.encode("ascii"), timeout=1)

