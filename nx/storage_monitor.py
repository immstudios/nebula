from nebulacore import *

from .agents import BaseAgent

__all__ = ["StorageMonitor"]

class StorageMonitor(BaseAgent):
    def main(self):
        storages_conf = config.get("storages", "all")
        for id_storage in storages:
            if type(storages_conf) == list and id_storage not in storages_conf:
                continue
            storage = storages[id_storage]

            if storage:
                storage_string = "{}:{}".format(config["site_name"], storage.id)
                storage_ident_path = os.path.join(storage.local_path,".nebula_root")

                if not (os.path.exists(storage_ident_path) and storage_string in [line.strip() for line in open(storage_ident_path).readlines()]):
                    try:
                        f = open(storage_ident_path, "a")
                        f.write(storage_string+"\n")
                        f.close()
                    except Exception:
                        if self.first_run:
                            logging.warning ("{} is mounted, but read only".format(storage))
                    else:
                        if self.first_run:
                            logging.info ("{} is mounted and root is writable".format(storage))
                continue


            logging.info ("{} is not mounted. Remounting.".format(storage))
            if not os.path.exists(storage.local_path):
                try:
                    os.mkdir(storage.local_path)
                except:
                    logging.error("Unable to create mountpoint for {}".format(storage))
                    continue

            self.mount(storage["protocol"], storage["path"], storage.local_path, storage["login"], storage["password"])

            if ismount(storage.local_path):
                logging.goodnews("{} remounted successfully".format(storage))
            else:
                logging.warning("{} remounting failed".format(storage))


    def mount(self, protocol, source, destination, username="", password=""):
        if protocol == "samba":
            if username and password:
                credentials = "user="+username+",pass="+password
            else:
                credentials = ""
            host = source.split("/")[2]
            cmd = "mount.cifs {} {} -o '{}'".format(source, destination, credentials)
        elif protocol == NFS:
            cmd = "mount.nfs {} {}".format(source, destination)
        else:
            return

        logging.debug("Executing:", cmd)
        c = Shell(cmd)
        if c.retcode:
            logging.error(c.stderr().read())

