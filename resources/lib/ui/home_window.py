import xbmc
from xbmcgui import Dialog
from xbmcaddon import Addon
import typing
from ui.login_dialog import LoginDialogWindow
from util.const import ADDON_PATH, loadConfig
from .common_window import CommonWindowXML
from .video_index_window import VideoIndexWindow
from util.api import Api

class HomeWindow(CommonWindowXML):

    class Config:
        season_type: typing.Any

    config: Config
    login_data: typing.Any

    @staticmethod
    def new() -> "HomeWindow":
        return HomeWindow("home_window.xml", ADDON_PATH)

    def __init__(
        self,
        xmlFilename: str,
        scriptPath: str,
        defaultSkin: str = "Default",
        defaultRes: str = "720p",
        isMedia: bool = False,
    ) -> None:
        super().__init__(xmlFilename, scriptPath, defaultSkin, defaultRes, isMedia)

    def onInit(self) -> None:
        if self.inited:
            return
        super().onInit()

        self.config = self.Config()
        self.config.season_type = loadConfig("season_type.json")

        for item in self.config.season_type:
            button = self.getButton(100 + item["st"])
            button.setLabel(item["name"])

        self.login_data = (
            Api.get_session()
            .get("https://api.bilibili.com/x/web-interface/nav")
            .json()["data"]
        )
        login_button = self.getButton(99)
        if self.login_data["isLogin"]:
            login_button.setLabel("注销")

    def onClick(self, controlId: int) -> None:
        if controlId == 99:
            if self.login_data["isLogin"]:
                exit = Dialog().yesno("注销", "是否要注销登录？")
                if exit:
                    session = Api.get_session()
                    session.post(
                        "https://passport.bilibili.com/login/exit/v2",
                        data={
                            "biliCSRF": session.cookies.get("bili_jct"),
                        },
                    )
                    Addon().setSettingString("cookies", "{}")
                    self.inited = False
                    self.onInit()
            else:
                window = LoginDialogWindow.new()
                window.doModal()
                self.inited = False
                self.onInit()
        elif controlId in range(100, 110):
            window = VideoIndexWindow.new(controlId - 100)
            window.doModal()
        else:
            super().onClick(controlId)
