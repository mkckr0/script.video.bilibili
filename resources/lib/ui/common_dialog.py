import typing
import xbmcgui

T = typing.TypeVar("T")

class CommonXMLDialog(xbmcgui.WindowXMLDialog):

    inited: bool = False

    def onInit(self) -> None:
        if not self.inited:
            self.inited = True
    
    def getButton(self, id: int) -> xbmcgui.ControlButton:
        return typing.cast(xbmcgui.ControlButton, self.getControl(id))

    def getContainer(self, id: int) -> xbmcgui.ControlList:
        return typing.cast(xbmcgui.ControlList, self.getControl(id))
     
    def getControl2(self, id: int, cls: typing.Type[T]) -> T:
        return typing.cast(cls, self.getControl(id))