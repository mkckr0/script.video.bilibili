import json
from platform import python_version
import xbmc
from ui.home_window import HomeWindow
from ui.video_index_window import VideoIndexWindow
from ui.media_info_window import MediaInfoWindow
import util.mpd_server as mpd_server

if __name__ == "__main__":
    xbmc.log(f"Python version: {python_version()}", xbmc.LOGINFO)

    try:
        mpd_server.start()

        window = HomeWindow.new()
        # window = VideoIndexWindow.new(1)
        # window = MediaInfoWindow.new("28339259")
        # window = MediaInfoWindow.new("28339083")

        window.doModal()
    except:
        raise
    finally:
        mpd_server.stop()