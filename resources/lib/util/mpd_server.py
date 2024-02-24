from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
import re
from socketserver import TCPServer
from threading import Thread
import traceback
from urllib.parse import parse_qsl, urlparse
import xbmc
from xbmcaddon import Addon
from .const import ADDON_ID
from . import mpd


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        url = urlparse(self.path)
        pattern = re.compile("^/manifest_[\\d\\w]+.mpd$")
        try:
            if pattern.match(url.path):
                manifest_data = mpd.get_mpd(dict(parse_qsl(qs=url.query)))
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/dash+xml")
                self.end_headers()
                self.wfile.write(manifest_data)
            else:
                self.send_response(HTTPStatus.NOT_FOUND)
                self.end_headers()
        except Exception:
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
            self.end_headers()
            xbmc.log(traceback.format_exc(), xbmc.LOGERROR)

    def do_HEAD(self):
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/dash+xml")
        self.end_headers()


def _startTcpServer(server: TCPServer):
    try:
        server.serve_forever()
    except Exception:
        # xbmc.log(traceback.format_exc())
        pass


_server_inst: TCPServer
_server_thread: Thread

def start():
    global _server_inst
    global _server_thread
    port = Addon().getSettingInt("mpd_port")
    _server_inst = TCPServer(("127.0.0.1", port), SimpleHTTPRequestHandler)
    xbmc.log(f"{ADDON_ID} bind {_server_inst.server_address}", xbmc.LOGINFO)
    _server_thread = Thread(target=_startTcpServer, args=[_server_inst])
    _server_thread.start()
    xbmc.log("MPD server started")

def stop():
    _server_inst.shutdown()
    _server_inst.server_close()
    _server_thread.join()
    xbmc.log("MPD server stop")