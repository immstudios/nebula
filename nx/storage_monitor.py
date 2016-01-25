from .core import *
from .connection import *
from .agents import BaseAgent

__all__ = ["StorageMonitor"]

class StorageMonitor(BaseAgent):
    def _main(self):
        for id_storage in storages:
            storage = storages[id_storage]
            if ismount(storage.local_path):
                storage_string = "{}:{}".format(config["site_name"], storage.id)
                storage_ident_path = os.path.join(storage.local_path,".nebula_root")

                if not (os.path.exists(storage_ident_path) and storage_string in [line.strip() for line in open(storage_ident_path).readlines()]):
                    try:
                        f = open(storage_ident_path, "a")
                        f.write(storage_string+"\n")
                        f.close()
                    except:
                        pass
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
        if protocol == CIFS:
            if username and password:
                credentials = ",username="+username+",password="+password
            else:
                credentials = ""
            host = source.split("/")[2]
            cmd = "mount -t cifs %s %s -o 'rw, iocharset=utf8, file_mode=0666, dir_mode=0777%s'" % (source,destination,credentials)
        elif protocol == NFS:
            cmd = "mount -t nfs %s %s"%(source,destination)
        elif protocol == FTP:
            cmd = "curlftpfs -o umask=0777,allow_other,direct_io %s:%s@%s %s"%(username,password,source,destination)
        else:
            return

        c = Shell(cmd)
        if c.retcode:
            logging.error(c.stderr().read())



