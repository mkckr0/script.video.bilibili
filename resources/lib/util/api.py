import json
import re
import typing
from bs4 import BeautifulSoup
import bs4
from requests import Session
import requests
from requests.adapters import HTTPAdapter
import xbmc
from xbmcaddon import Addon


class Api:
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    REFERER = "https://www.bilibili.com"

    __session: Session

    class MyHTTPAdapter(HTTPAdapter):
        def send(
            self, request: requests.PreparedRequest, **kwargs
        ) -> requests.Response:
            if "timeout" not in kwargs:
                kwargs["timeout"] = 3
            return super().send(request, **kwargs)

    @staticmethod
    def get_session(new_session: bool = False):
        try:
            _ = Api.__session
            if new_session:
                raise Exception("new_session")
        except:
            session = requests.Session()
            session.headers.update(
                {
                    "User-Agent": Api.USER_AGENT,
                    "Referer": Api.REFERER,
                }
            )
            cookies = json.loads(Addon().getSettingString("cookies"))
            session.cookies.update(cookies)
            # xbmc.log(f"cookies: {session.cookies.items()}")
            session.mount("http", Api.MyHTTPAdapter())
            session.mount("https", Api.MyHTTPAdapter())
            Api.__session = session
        return Api.__session

    @staticmethod
    def get_initial_state(url: str) -> typing.Any:
        res = Api.get_session().get(url)
        return Api.parse_initial_state(res.content)

    @staticmethod
    def parse_initial_state(content: bytes) -> typing.Any:
        html = BeautifulSoup(content, "html.parser")
        script = typing.cast(
            bs4.Tag,
            html.find(name="script", string=re.compile("window.__INITIAL_STATE__")),
        )
        script = script.string or ""
        data = json.loads(script[script.find("=") + 1 : script.find("};") + 1])
        return data
