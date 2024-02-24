import glob
import json
import os
import sqlite3
import typing
from xbmcaddon import Addon
from xbmcvfs import translatePath
import xbmc

ADDON_ID = Addon().getAddonInfo("id")
ADDON_PATH = translatePath(Addon().getAddonInfo("path"))
ADDON_PROFILE = translatePath(Addon().getAddonInfo("profile"))


def loadConfig(filename: str) -> typing.Any:
    with open(os.path.join(ADDON_PATH, "resources/data", filename), "rb") as ifile:
        return json.load(ifile)


def getResumePoint(url: str) -> typing.Optional[typing.Tuple[float, float]]:
    url = url.split("?")[0]
    pos = url.rfind("/")
    path = url[: pos + 1]
    filename = url[pos + 1 :]
    user_data = os.path.abspath(os.path.join(ADDON_PROFILE, *([os.path.pardir] * 2)))
    for file in glob.glob(os.path.join(user_data, "Database", "MyVideo*.db")):
        conn = sqlite3.connect(file)
        cur = conn.cursor()
        cur.execute(
            "select timeInSeconds, totalTimeInSeconds from bookmark where idFile = ("
            "select idFile from files where idPath = ("
            "select idPath from path where strPath = ?"
            ") and strFilename = ?"
            ") and type = 1;",
            (path, filename),
        )
        ret = cur.fetchone()
        if ret != None:
            return ret

    return None
