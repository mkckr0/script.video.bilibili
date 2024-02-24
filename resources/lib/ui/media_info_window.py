import time
import typing
from urllib.parse import urlencode
import xbmc, xbmcgui
from xbmcaddon import Addon
from xbmcgui import ListItem, Dialog
from util.const import ADDON_PATH, getResumePoint
from .common_window import CommonWindowXML
from util.api import Api


class MediaInfoWindow(CommonWindowXML):

    media_id: str
    media_info: typing.Any
    episode_info: typing.Any

    @staticmethod
    def new(media_id: str) -> "MediaInfoWindow":
        return MediaInfoWindow("media_info_window.xml", ADDON_PATH, media_id=media_id)

    def __init__(
        self,
        xmlFilename: str,
        scriptPath: str,
        defaultSkin: str = "Default",
        defaultRes: str = "720p",
        media_id: str = "",
    ) -> None:
        super().__init__(xmlFilename, scriptPath, defaultSkin, defaultRes)
        self.media_id = media_id

    def onInit(self) -> None:
        if self.inited:
            return
        super().onInit()

        # load media info
        # data = open(os.path.join(ADDON_PATH, "test/media_info.html"), "rb").read()
        data = Api.get_initial_state(
            f"https://www.bilibili.com/bangumi/media/md{self.media_id}"
        )
        self.media_info = data["mediaInfo"]

        # self.episode_info = json.load(open(os.path.join(ADDON_PATH, "test/section.json"), "rb"))["result"]
        self.episode_info = (
            Api.get_session()
            .get(
                "https://api.bilibili.com/pgc/web/season/section",
                params={"season_id": self.media_info["season_id"]},
            )
            .json()["result"]
        )

        media_info = self.media_info
        list_item = ListItem()
        list_item.setArt({"thumb": media_info["cover"]})
        list_item.setProperties(
            {
                "media_id": str(media_info["media_id"]),
                "release_date_show": media_info["publish"]["release_date_show"],
                "time_length_show": media_info["publish"]["time_length_show"],
                "styles": " ".join([style["name"] for style in media_info["styles"]]),
            }
        )
        tag: xbmc.InfoTagVideo = list_item.getVideoInfoTag()
        tag.setMediaType("movie")
        tag.setTitle(media_info["title"])
        tag.setTagLine(media_info["alias"])
        tag.setOriginalTitle(media_info["origin_name"])
        tag.setPlot(media_info["evaluate"])
        tag.setCountries([area["name"] for area in media_info["areas"]])
        if "rating" in media_info:
            tag.setRating(media_info["rating"]["score"], media_info["rating"]["count"])
        tag.setPremiered(media_info["publish"]["pub_date"])
        # tag.setPlaycount(media_info["stat"]["views"])
        container = self.getContainer(100)
        container.reset()
        container.addItem(list_item)

        # season list
        container = self.getContainer(102)
        container.reset()
        if len(media_info["seasons"]) > 1:
            selected = 0
            for index, season in enumerate(media_info["seasons"]):
                list_item = ListItem(season["season_title"])
                list_item.setProperty("media_id", str(season["media_id"]))
                if str(season["media_id"]) == self.media_id:
                    list_item.select(True)
                    selected = index
                container.addItem(list_item)
            container.selectItem(selected)

        # episode list
        container = self.getContainer(103)
        container.reset()
        data = self.episode_info
        if "main_section" in data:
            episodes = data["main_section"]["episodes"]
            for episode in episodes:
                list_item = ListItem()
                list_item.setLabel2(episode["badge"])
                tag = list_item.getVideoInfoTag()
                tag.setTitle(episode["title"])
                tag.setTvShowTitle(episode["long_title"])
                list_item.setArt({"thumb": episode["cover"]})
                list_item.setProperties(
                    {
                        "avid": episode["aid"],
                        "cid": episode["cid"],
                        "ep_id": episode["id"],
                    }
                )
                container.addItem(list_item)

    def onClick(self, controlId: int) -> None:
        if controlId == 102:
            list_item = self.getContainer(102).getSelectedItem()
            new_media_id = list_item.getProperty("media_id")
            if self.media_id != new_media_id:
                self.media_id = new_media_id
                self.inited = False
                self.onInit()
        elif controlId == 103:
            list_item = self.getContainer(103).getSelectedItem()

            play_item = xbmcgui.ListItem()
            play_item.setMimeType("application/dash+xml")
            play_item.setContentLookup(False)
            play_item.setProperty("inputstream", "inputstream.adaptive")
            play_item.setProperty("inputstream.adaptive.manifest_type", "mpd")
            play_item.setProperty(
                "inputstream.adaptive.stream_selection_type", "manual-osd"
            )

            play_item.setProperty(
                "inputstream.adaptive.stream_headers",
                f"UserAgent={Api.USER_AGENT}&Referer={Api.REFERER}",
            )
            mpd_port = Addon().getSettingInt("mpd_port")
            params = {
                "avid": list_item.getProperty("avid"),
                "cid": list_item.getProperty("cid"),
                "ep_id": list_item.getProperty("ep_id"),
            }
            unique_id = "avid_" + list_item.getProperty("avid")
            url = f"http://127.0.0.1:{mpd_port}/manifest_{unique_id}.mpd?{urlencode(params)}"

            media_info = self.media_info
            play_item.setArt({"thumb": list_item.getArt("thumb")})
            tag: xbmc.InfoTagVideo = play_item.getVideoInfoTag()
            tag.setTitle(media_info["title"])
            tag.setTagLine(media_info["alias"])
            tag.setOriginalTitle(media_info["origin_name"])
            tag.setPlot(media_info["evaluate"])

            resume_point = getResumePoint(url)
            if resume_point:
                resume_time = time.strftime("%H:%M:%S", time.gmtime(resume_point[0]))
                selected = Dialog().contextmenu(
                    [
                        xbmc.getLocalizedString(12022).format(resume_time), # Resume from {0:s}
                        xbmc.getLocalizedString(12021), # Play from beginning
                    ]
                )
                if selected == -1:
                    return
                elif selected == 0:
                    play_item.setProperty("StartOffset", "-0.001")
            xbmc.Player().play(url, play_item)

        else:
            super().onClick(controlId)
