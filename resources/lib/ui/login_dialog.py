import json
import os
from threading import Thread
import time
import qrcode
import xbmc, xbmcgui
from xbmcaddon import Addon
from util.const import ADDON_PATH
from util.api import Api
from .common_dialog import CommonXMLDialog
from util import cache


class LoginDialogWindow(CommonXMLDialog):

    qrcode_key: str
    qrcode_path: str
    label: xbmcgui.ControlLabel
    cancel_flag: bool
    thread: Thread

    @staticmethod
    def new() -> "LoginDialogWindow":
        return LoginDialogWindow("login_dialog.xml", ADDON_PATH)

    def __init__(
        self,
        xmlFilename: str,
        scriptPath: str,
        defaultSkin: str = "Default",
        defaultRes: str = "720p",
    ) -> None:
        super().__init__(xmlFilename, scriptPath, defaultSkin, defaultRes)

    def onInit(self) -> None:
        if self.inited:
            return
        super().onInit()

        session = Api.get_session()
        cache.clear_cache("qrcode_*.png")
        data = session.get(
            "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
        ).json()["data"]
        qr = qrcode.make(data["url"])
        self.qrcode_key = data["qrcode_key"]
        self.qrcode_path = os.path.join(
            cache.CACHE_PATH, f"qrcode_{self.qrcode_key}.png"
        )
        qr.save(self.qrcode_path)

        # self.qrcode_path = os.path.join(cache.CACHE_PATH, "qrcode_a4fce016a753ade6aaf3969e97b7eb22.png")
        # self.qrcode_key = "a4fce016a753ade6aaf3969e97b7eb22"

        self.thread = Thread(target=self.loginPoll)
        self.thread.start()

        image = self.getControl2(100, xbmcgui.ControlImage)
        image.setImage(self.qrcode_path)

        self.label = self.getControl2(101, xbmcgui.ControlLabel)
        self.label.setLabel("")

    def doModal(self) -> None:
        super().doModal()
        self.cancel_flag = True
        self.thread.join()

    def loginPoll(self):
        session = Api.get_session()
        self.cancel_flag = False
        while not self.cancel_flag:
            time.sleep(2)
            xbmc.log("loginPoll")
            data = session.get(
                "https://passport.bilibili.com/x/passport-login/web/qrcode/poll",
                params={"qrcode_key": self.qrcode_key},
            ).json()["data"]
            xbmc.log(f"loginPoll {data}")
            if data["message"] == "未扫码":
                continue
            elif data["message"] == "二维码已失效":
                self.label.setLabel(data["message"])
                break
            elif data["message"] == "二维码已扫码未确认":
                self.label.setLabel(data["message"])
                continue
            elif data["message"] == "":  # 登录成功
                self.label.setLabel("登录成功")

                addon = Addon()
                addon.setSettingString("poll_res", json.dumps(data, ensure_ascii=True))
                addon.setSettingString(
                    "cookies",
                    json.dumps(session.cookies.items(), ensure_ascii=True),
                )

                time.sleep(2)
                self.close()
                break
            else:
                self.label.setLabel(data["message"])
                break
