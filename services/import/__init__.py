from nebula import *


def temp_file(id_storage, ext):
    temp_dir = os.path.join(
            storages[id_storage].local_path,
            ".nx",
            "creating"
        )
    if not os.path.isdir(temp_dir):
        try:
            os.makedirs(temp_dir)
        except Exception:
            log_traceback()
            return False
    return get_temp(ext, temp_dir)



def mk_error(fname, message):
    log_file_path = os.path.splitext(fname.path)[0] + ".error.txt"
    try:
        old_message = open(log_file_path).read()
    except:
        old_message = ""
    if old_message != message:
        logging.error("{} : {}".format(fname.base_name, message))
        with open(log_file_path, "w") as f:
            f.write(message)


def version_backup(asset):
    target_dir = os.path.join(
            storages[asset["id_storage"]].local_path,
            ".nx",
            "versions",
            "{:04d}".format(int(asset.id/1000)),
            "{:d}".format(asset.id)
        )

    target_path = "{:d}{}".format(
            int(asset["mtime"]),
            os.path.splitext(asset.file_path)[1]
        )

    if not os.path.isdir(target_dir):
        try:
            os.makedirs(target_dir)
        except IOError:
            pass
    try:
        os.rename(
                asset.file_path,
                target_path
            )
    except IOError:
        logging.warning("Unable to create version backup of {}".format(asset))




def do_import(parent, import_file, asset):

    probe = mediaprobe(import_file)
    match = True
    for condition in parent.conditions:
        value = parent.conditions[condition]
        print ("check", value, probe.get(condition, None))
        if value != probe.get(condition, None):
            match = False
            break

    print("match", match)
    if match:
        logging.info("Fast importing {} to {}".format(import_file, asset))
    else:
        logging.info("Importing {} to {}".format(import_file, asset))










class Service(BaseService):
    def on_init(self):
        ## TODO: Load this from service settings
        self.import_storage = 1
        self.import_dir = "import-test.dir"
        self.backup_dir = "backup.dir"
        self.identifier = "id/main"
        self.exts = [f for f in file_types.keys() if file_types[f] == VIDEO]
        self.versioning = True

        self.conditions = {
            "video/codec" : "dnxhd"
        }

        self.profile = {
            "fps" : 25,
            "loudness" : -23.0,
            "container" : "mov",
            "width" : 1920,
            "height" : 1080,
            "pixel_format" : "yuv422p",
            "video_codec" : "dnxhd",
            "video_bitrate" : "36M",
            "audio_codec" : "pcm_s16le",
            "audio_sample_rate" : 48000
        }

        self.filesizes = {}
        import_storage_path = storages[self.import_storage].local_path
        self.import_dir = os.path.join(import_storage_path, self.import_dir)
        self.backup_dir = os.path.join(import_storage_path, self.backup_dir)


    def on_main(self):
        if not self.import_dir:
            return

        if not os.path.isdir(self.import_dir):
            logging.error("Import directory does not exist. Shutting down service.")
            self.import_path = False
            self.shutdown(no_restart=True)
            return

        db = DB()
        for import_file in get_files(
                self.import_dir,
                exts=self.exts,
            ):

            idec = import_file.base_name
            try:
                with import_file.open("rb") as f:
                    f.seek(0,2)
                    fsize = f.tell()
            except IOError:
                logging.debug("Import file {} is busy. Skipping.".format(import_file.base_name))
                continue

            if not (import_file.path in self.filesizes and self.filesizes[import_file.path] == fsize):
                self.filesizes[import_file.path] = fsize
                logging.debug("New file '{}' detected".format(import_file.base_name))
                continue

            db.query("SELECT meta FROM assets WHERE meta->>%s = %s", [self.identifier, idec])
            for meta, in db.fetchall():
                asset = Asset(meta=meta, db=db)

                if not (asset["id_storage"] and asset["path"]):
                    self.mk_error(import_file, "This file has no target path specified.")
                    continue

                do_import(self, import_file, asset)
                break
            else:
                mk_error(import_file, "This file is not expected.")


        for fname in os.listdir(self.import_dir):
            if not fname.endswith(".error.txt"):
                continue
            idec = fname.replace(".error.txt", "")
            if not idec in [os.path.splitext(f)[0] for f in os.listdir(self.import_dir)]:
                os.remove(os.path.join(self.import_dir, fname))
