from nx import *
from .common import Probe, guess_aspect

class FFProbe(Probe):
    title = "FFProbe"

    def accepts(self, asset):
        return asset["content_type"] in [VIDEO, AUDIO, IMAGE]

    def work(self, asset):
        old_meta = asset.meta
        fname = asset.file_path
        try:
            dump = ffprobe(fname)
            streams = dump["streams"]
            format  = dump["format"]
        except Exception:
            logging.error("Unable to parse media metadata of {}".format(asset))
            asset["meta_probed"] = 1
            return asset


        asset["file/format"]   = format.get("format_name", "")
        asset["duration"] = format.get("duration", 0)

        ## Streams

        at_atrack  = 1         # Audio track identifier (A1, A2...)

        for stream in streams:
            if stream["codec_type"] == "video" and asset["content_type"] in [VIDEO, IMAGE]: # ignore mp3 album art etc.

                asset["video/fps"]          = stream.get("r_frame_rate","")
                asset["video/codec"]        = stream.get("codec_name","")
                asset["video/pixel_format"] = stream.get("pix_fmt", "")
                asset["video/color_range"] = stream.get("color_range", "")
                asset["video/color_space"] = stream.get("color_space", "")

                #
                # Duration (if not provided in container metadata)
                #

                if not asset["duration"]:
                    dur = float(stream.get("duration",0))
                    if dur:
                        asset["duration"] = dur
                    else:
                        if stream.get("nb_frames", "").isnumeric():
                            if asset["video/fps"]:
                                asset["duration"] = int(stream["nb_frames"]) / asset[fps]

                #
                # Frame size
                #

                try:
                    w, h = int(stream["width"]), int(stream["height"])
                except Exception:
                    w = h = 0

                if w and h:
                    asset["video/width"]  = w
                    asset["video/height"] = h

                    dar = stream.get("display_aspect_ratio", False)
                    if dar:
                        asset["video/aspect_ratio"] = guess_aspect(*[int(i) for i in dar.split(":")])

                    if asset["video/aspect_ratio"] == "0":
                        asset["video/aspect_ratio"] = guess_aspect(w, h)


            elif stream["codec_type"] == "audio":
                asset["audio/codec"] == stream

        #
        # Descriptive metadata (tags)
        #

        content_type = asset["content_type"]
        if "tags" in format.keys() and not "meta_probed" in asset.meta:
            if content_type == AUDIO:
                tag_mapping = {
                                "title"   : "title",
                                "artist"  : "role/performer",
                                "composer": "role/composer",
                                "album"   : "album",
                              }
            else:
                tag_mapping = {
                                "title" : "title"
                                }

            for tag in format["tags"]:
                value = format["tags"][tag]
                if tag in tag_mapping:
                    if not tag_mapping[tag] in asset.meta or tag == "title": # Only title should be overwriten if exists. There is a reason
                        asset[tag_mapping[tag]] = value
                elif tag in ["track","disc"] and content_type == AUDIO:
                    if not "album/%s"%tag in asset.meta:
                        asset["album/%s"%tag] = value.split("/")[0]
                elif tag == "genre" and content_type == AUDIO:
                    # Ultra mindfuck
                    NX_MUSIC_GENRES = [
                                        "Alt Rock",
                                        "Electronic",
                                        "Punk Rock",
                                        "Pop",
                                        "Rock",
                                        "Metal",
                                        "Hip Hop",
                                        "Demoscene",
                                        "Emo"
                                        ]

                    for genre in NX_MUSIC_GENRES:
                        genre_parts = genre.lower().split()
                        for g in genre_parts:
                            if value.lower().find(g) > -1:
                                continue
                            break
                        else:
                            if not "genre/music" in asset.meta:
                                asset["genre/music"] = genre
                            break
                    else:
                        if not "genre/music" in asset.meta:
                            asset["genre/music"] = value
            asset["meta_probed"] = 1

        return asset

