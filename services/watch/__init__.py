from nebula import *

class Service(BaseService):
    def on_init(self):
        self.mirrors = self.settings.findall("mirror")
        self.ignore = []

    def on_main(self):
        db = DB()
        abp_cache = {}
        for mirror in self.mirrors:

            #
            # Mirror settings
            #

            id_storage    = int(mirror.find("id_storage").text)
            rel_path      = mirror.find("path").text
            storage_path  = storages[mstorage].local_path
            input_path    = os.path.join(storage_path, rel_path)

            try:    filters = mirror.find("filters").findall("filter")
            except: filters = []

            try:    mrecursive = int(mirror.find("recursive").text)
            except: mrecursive = 0

            try:    mhidden = int(mirror.find("hidden").text)
            except: mhidden = 0

            #
            # Browse files
            #

            now = time.time()
            for input_path in get_files(input_path, recursive=mrecursive, hidden=mhidden):

                asset_path = os.path.normpath(f.replace(storage_path ,""))
                asset_path = apath.lstrip("/")
                if not asset_path:
                    continue

                try:
                    content_type = file_types[os.path.splitext(f)[1][1:].lower()]
                except KeyError:
                    continue

                if filters:
                    for f in filters:
                        if CONTENT_TYPES.get(f.text.lower(), "blah blah") == content_type:
                          break
                    else:
                        continue

                if now - abp_cache.get("{}|{}".format(id_storage,asset_path), 0) > 600:
                    if asset_by_path(id_storage, asset_path, db=db):
                        continue

                if (id_storage, asset_path) in self.ignore:
                    continue

                logging.debug("Found new file '{}'".format(apath))

                asset = Asset(db=db)
                asset["id_storage"]    = id_storage
                asset["path"]          = asset_path
                asset["title"]         = file_to_title(apath)
                asset["content_type"]  = content_type
                asset["media_type"]    = FILE
                asset["status"]        = CREATING

                asset.load_sidecar_metadata()

                for mt in mirror.findall("meta"):
                    try:
                        if mt.attrib["type"] == "script":
                            exec "asset[mt.attrib[\"tag\"]] = %s"% (mt.text or "")
                        else:
                            raise Exception
                    except:
                        asset[mt.attrib["tag"]] = mt.text or ""

                failed = False
                for post_script in mirror.findall("post"):
                    try:
                        exec(post_script.text)
                    except:
                        log_traceback("Error executing post-script on {}".format(asset))
                        failed = True

                if not failed:
                    asset.save()
                    logging.info("Created %s from %s"%(asset, apath))
                else:
                    logging.info("Post script failed. Ignoring file.")
                    self.ignore.append((mstorage, apath))
