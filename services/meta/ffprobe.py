from nx import *
from nx.mediaprobe import mediaprobe

from .common import Probe


class FFProbe(Probe):
    title = "FFProbe"

    def accepts(self, asset):
        return asset["content_type"] in [VIDEO, AUDIO, IMAGE]

    def __call__(self, asset):
        meta = mediaprobe(asset.file_path)
        if not meta:
            return False

        for key, value in meta.items():

            # Only update auto-generated title
            if key == "title":
                if value == get_base_name(asset.file_path):
                    continue

            # Do not update descriptive metadata
            elif meta_types[key]["ns"] == "m" and asset[key]:
                logging.warning(f"skipping update {key} to {value}")
                continue

            logging.info(f"updating {key} to {value}")
            asset[key] = value

        return asset

