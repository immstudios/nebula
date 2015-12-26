from core import *
from .db import *
from .agents import BaseMonitor


class StorageMonitor(BaseMonitor):
    def main(self):
        for id_storage in storages:
            storage = storages[id_storage]
            if ismount(storage.get_path()): 
                storage_string = "{}:{}".format(config["site_name"], storage.id_storage)
                storage_ident_path = os.path.join(storage.get_path(),".nebula_root")

                if not (os.path.exists(storage_ident_path) and storage_string in [line.strip() for line in open(storage_ident_path).readlines()]):
                    try:
                        f = open(storage_ident_path, "a")
                        f.write(storage_string+"\n")
                        f.close()
                    except: 
                        pass
                continue

            logging.info ("Storage %s (%s) is not mounted. Remounting."%(storage.id_storage,storage.title))

            if not os.path.exists(storage.get_path()):
                try:     
                    os.mkdir(storage.get_path())
                except:  
                    logging.error("Unable to create mountpoint for storage %s (%s)"%(storage.id_storage,storage.title))   
                    continue
            
            self.mount(storage.protocol, storage.path, storage.get_path(), storage.login, storage.password)
            
            if ismount(storage.get_path()):     
                logging.goodnews("Storage %s (%s) remounted successfully"%(storage.id_storage,storage.title))
            else:                     
                logging.warning ("Storage %s (%s) remounting failed"%(storage.id_storage,storage.title)) 


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

        c = shell(cmd) 
        print c.stderr().read()
