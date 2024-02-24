from copy import deepcopy
import typing
import xbmc
from xbmcgui import Dialog, ListItem
from util.const import ADDON_PATH, loadConfig
from util import cache
from util.api import Api
from .common_window import CommonWindowXML
from .media_info_window import MediaInfoWindow


class VideoIndexWindow(CommonWindowXML):

    class State:
        filter: typing.List[int]
        order: int  # 排序类型
        sort: int  # 排序升降

        def setdefault(self, default: "VideoIndexWindow.State"):
            for key, value in default.__dict__.items():
                self.__dict__.setdefault(key, value)

    class Config:
        filter: typing.Any
        order: typing.Any
        sort: typing.Any
        season_type: typing.Any

    inited: bool = False
    state: State
    default_state: State
    config: Config
    page: int
    page_size: int
    total: int
    has_next_page: bool
    st: int

    @staticmethod
    def new(st: int) -> "VideoIndexWindow":
        return VideoIndexWindow("video_index_window.xml", ADDON_PATH, st=st)

    def __init__(
        self,
        xmlFilename: str,
        scriptPath: str,
        defaultSkin: str = "Default",
        defaultRes: str = "720p",
        st: int = 0,
    ) -> None:
        super().__init__(xmlFilename, scriptPath, defaultSkin, defaultRes)
        self.st = st

    def doModal(self) -> None:
        super().doModal()
        cache.set_state(f"video_index_window_state_{self.st}", self.state)

    def onInit(self):
        if self.inited:
            return
        super().onInit()

        # load config
        self.config = self.Config()
        self.config.season_type = loadConfig("season_type.json")
        self.config.sort = loadConfig("sort.json")
        season_type = next(e for e in self.config.season_type if e["st"] == self.st)
        data = Api.get_initial_state(
            f"https://www.bilibili.com/{season_type['key']}/index"
        )
        self.config.filter = data["filters"]
        self.config.order = data["orders"]

        # default state
        self.default_state = self.State()
        self.default_state.filter = [0] * len(self.config.filter)
        self.default_state.order = 0
        self.default_state.sort = 0

        # load state
        self.state = cache.get_state(f"video_index_window_state_{self.st}", self.State)
        self.state.setdefault(self.default_state)

        # load video index data
        self.page = 0
        self.page_size = 20
        self.total = 0
        self.has_next_page = True

        self.updateFilterUI()
        self.updateOrderUI()
        self.updateVideoList()

    def onClick(self, controlId: int) -> None:
        if controlId in range(100, 109):  # select filter
            index = controlId - 100
            item = self.config.filter[index]
            selected = Dialog().select(
                item["title"],
                [x["name"] for x in item["list"]],
                preselect=self.state.filter[index],
            )
            if selected == -1:
                return
            self.state.filter[index] = selected
            self.updateFilterUI()
            self.updateVideoList()
        elif controlId == 109:  # reset filter
            self.state.filter = deepcopy(self.default_state.filter)
            self.updateFilterUI()
            self.updateVideoList()
        elif controlId == 110:  # select order
            selected = Dialog().select(
                "类型",
                [e["title"] for e in self.config.order],
                preselect=self.state.order,
            )
            if selected == -1:
                return
            self.state.order = selected
            self.updateOrderUI()
            self.updateVideoList()
        elif controlId == 111:  # next sort
            self.state.sort = (self.state.sort + 1) % len(self.config.sort)
            self.updateOrderUI()
            self.updateVideoList()
        elif controlId == 112:  # reset order
            self.state.order = self.default_state.order
            self.state.sort = self.default_state.sort
            self.updateOrderUI()
            self.updateVideoList()
        elif controlId == 200:  # container click
            container = self.getContainer(200)
            if (
                self.has_next_page
                and container.getSelectedPosition() == container.size() - 1
            ):
                self.updateVideoList(False)
                return
            list_item = container.getSelectedItem()
            window = MediaInfoWindow.new(media_id=list_item.getProperty("media_id"))
            window.doModal()
        else:
            super().onClick(controlId)

    def updateFilterUI(self):
        # hide all filter button
        for id in range(100, 109):
            button = self.getButton(id)
            button.setVisible(False)

        # enable filter button
        for index, item in enumerate(self.config.filter):
            button = self.getButton(100 + index)
            button.setLabel(
                label=item["title"],
                label2=item["list"][self.state.filter[index]]["name"],
            )
            button.setVisible(True)

    def updateOrderUI(self):
        # set order and sort
        button = self.getButton(110)
        button.setLabel(
            label="类型", label2=self.config.order[self.state.order]["title"]
        )
        button = self.getButton(111)
        button.setLabel(label="升降", label2=self.config.sort[self.state.sort]["name"])

    def updateVideoList(self, reset: bool = True):
        container = self.getContainer(200)
        replace_last = False
        selected = container.getSelectedPosition()
        if reset:
            self.page = 0
            self.total = 0
            container.reset()
        elif container.size() > 0:
            replace_last = True
        video_list = self.pullNextPage()
        for index, video in enumerate(video_list):
            if replace_last and index == 0:
                list_item = container.getListItem(container.size() - 1)
            else:
                list_item = ListItem()
                container.addItem(list_item)
            list_item.setLabel(video["title"])
            list_item.setLabel2(video["subTitle"])
            list_item.setArt(
                {
                    "icon": video["cover"],
                    # "poster": video["cover"],
                }
            )
            tag: xbmc.InfoTagVideo = list_item.getVideoInfoTag()
            tag.setTitle(video["title"])
            tag.setTagLine(video["subTitle"])
            if video["score"] != "":
                tag.setRating(float(video["score"]))
            list_item.setProperty("media_id", str(video["media_id"]))

        if self.has_next_page:
            list_item = ListItem("加载更多")
            container.addItem(list_item)

        if not reset:
            container.selectItem(selected)

    def pullNextPage(self):
        params = {}
        for index, item in enumerate(self.config.filter):
            key = item["key"]
            value = item["list"][self.state.filter[index]]["value"]
            params[key] = value
        params.update(
            {
                "st": self.st,
                "season_type": self.st,
                "order": self.config.order[self.state.order]["key"],
                "sort": self.config.sort[self.state.sort]["value"],
                "page": self.page + 1,
                "pagesize": self.page_size,
                "type": 1,
            }
        )
        session = Api.get_session()
        res = session.get(
            f"http://api.bilibili.com/pgc/season/index/result",
            params=params,
        ).json()
        data = res["data"]
        self.page = data["num"]
        self.total = data["total"]
        self.has_next_page = bool(data["has_next"])
        return data["list"]
