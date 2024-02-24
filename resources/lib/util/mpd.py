import xml.etree.ElementTree as ET
from util.api import Api

def _get_stream_attrib(id, stream_info):
    frameRate = _decimal_to_fraction(stream_info["frameRate"])
    attrib = {
        "id": str(id),
        "mimeType": stream_info["mimeType"],
        # "codecid": str(stream_info["codecid"]),
        "codecs": stream_info["codecs"],
        "frameRate": frameRate,
        "bandwidth": str(stream_info["bandwidth"]),
        # "size": str(stream_info["size"]),
        "width": str(stream_info["width"]),
        "height": str(stream_info["height"]),
        "sar": stream_info["sar"],
        "startWithSAP": str(stream_info["startWithSAP"]),
    }
    for k, v in attrib.copy().items():
        if k != "id" and (v in {"", "0"}):
            attrib.pop(k)
    return attrib


def _fill_stream_set(id, stream_set, stream_info):
    for index, info in enumerate(stream_info):
        audio_stream = ET.SubElement(stream_set, "Representation")
        audio_stream.attrib = _get_stream_attrib(f"{id}_{index}", info)
        ET.SubElement(audio_stream, "BaseURL").text = info["baseUrl"]
        seg_base = ET.SubElement(audio_stream, "SegmentBase")
        seg_base.attrib = {
            "indexRange": info["SegmentBase"]["indexRange"],
        }
        ET.SubElement(seg_base, "Initialization").attrib = {
            "range": info["SegmentBase"]["Initialization"],
        }


def _decimal_to_fraction(src: str) -> str:
    src = src.lstrip("0")
    dot_pos = src.find(".")
    if dot_pos != -1:
        src = src.rstrip("0")
    if src in {"", "."}:
        return "0"
    if dot_pos == -1:
        return src
    demoninator = pow(10, len(src) - 1 - dot_pos)
    numerator = src.replace(".", "")
    return f"{numerator}/{demoninator}"


def get_mpd(params: dict):
    session = Api.get_session(True)
    params.update(
        {
            "support_multi_audio": "true",
            "qn": "120",
            "fnver": "0",
            "fnval": "4048",
            "fourk": "1",
            "gaia_source": "",
            "from_client": "BROWSER",
            "voice_balance": "1",
            "drm_tech_type": "2",
        }
    )
    res = session.get(
        "https://api.bilibili.com/pgc/player/web/v2/playurl",
        params=params,
    )
    # xbmc.log(f"request url: {res.request.url}")
    data = res.json()
    # xbmc.log(f"response: {data}")

    video_info = data["result"]["video_info"]
    dash = video_info["dash"]
    del data

    # if video_info["has_dolby"]:
    #     for stream in dash["dolby"]["audio"]:
    #         stream["mimeType"] = stream.pop("mime_type")
    #         stream["frameRate"] = stream.pop("frame_rate")
    #         stream["startWithSAP"] = stream.pop("start_with_sap")
    #         stream["baseUrl"] = stream.pop("base_url")
    #         stream["SegmentBase"] = stream.pop("segment_base")
    #         stream["SegmentBase"]["indexRange"] = stream["SegmentBase"].pop("index_range")
    #         stream["SegmentBase"]["Initialization"] = stream["SegmentBase"].pop("initialization")
    #     dash["audio"].append(stream)

    MPD = ET.Element("MPD")
    MPD.attrib = {
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xmlns": "urn:mpeg:dash:schema:mpd:2011",
        "xsi:schemaLocation": "urn:mpeg:dash:schema:mpd:2011 DASH-MPD.xsd",
        "type": "static",
        "profiles": "urn:mpeg:dash:profile:isoff-on-demand:2011",
        "mediaPresentationDuration": f"PT{dash['duration']}S",
        "minBufferTime": f"PT{dash['minBufferTime']}S",
    }

    period = ET.SubElement(MPD, "Period")
    video_stream_set = ET.SubElement(
        period, "AdaptationSet", id="0", contentType="video"
    )
    _fill_stream_set(0, video_stream_set, dash["video"])
    audio_stream_set = ET.SubElement(
        period, "AdaptationSet", id="1", contentType="audio"
    )
    _fill_stream_set(1, audio_stream_set, dash["audio"])

    etree = ET.ElementTree(MPD)
    # ET.indent(etree)
    s = ET.tostring(MPD, xml_declaration=True)
    return s


# test
if __name__ == "__main__":
    pass
