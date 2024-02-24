import typing
import xbmcgui

class CommonWindowXML(xbmcgui.WindowXML):

    inited: bool = False

    def onInit(self) -> None:
        if not self.inited:
            self.inited = True
    
    def getButton(self, id: int) -> xbmcgui.ControlButton:
        return typing.cast(xbmcgui.ControlButton, self.getControl(id))

    def getContainer(self, id: int) -> xbmcgui.ControlList:
        return typing.cast(xbmcgui.ControlList, self.getControl(id))