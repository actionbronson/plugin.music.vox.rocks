import xbmc, xbmcaddon
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

addon = xbmcaddon.Addon(id="plugin.music.vox.rocks")

# Kodi calls HEAD to get artwork details but VOX's servers only accept GETs, hence this
# super minimalist proxy.

class VoxHTTPHandler(BaseHTTPRequestHandler):
    def _prep_resp(self, url, write_content: bool):
        if not(url) or url == "":
            self.send_response_only(404)
            return
        xbmc.log(f"Doing a GET on: {url}", xbmc.LOGINFO)
        resp = requests.get(url)
        resp.raise_for_status()
        self.send_response(int(resp.status_code))
        headers = resp.headers
        xbmc.log(f"Header passthrough: {str(headers)}", xbmc.LOGDEBUG)
        for header_name in headers.keys():
            self.send_header(header_name, headers[header_name])
        self.end_headers()
        if write_content:
            xbmc.log(f"Also writing content.", xbmc.LOGDEBUG)
            xbmc.log(f"Content: {str(resp.content)}", xbmc.LOGINFO)
            self.wfile.write(resp.content)

    def do_GET(self):
        artwork_url = self.path[1:]
        xbmc.log(f"Caught a GET on '{artwork_url}'", xbmc.LOGINFO)
        self._prep_resp(artwork_url, True)
        
    def do_HEAD(self):
        artwork_url = self.path[1:]
        xbmc.log(f"Caught a HEAD on '{artwork_url}'", xbmc.LOGINFO)
        self._prep_resp(artwork_url, False)

def start_http():
    server_address = ('localhost', int(addon.getSetting('proxy_port')))
    httpd = HTTPServer(server_address, VoxHTTPHandler)
    xbmc.log(f"starting http server on localhost port: {addon.getSetting('proxy_port')}", xbmc.LOGINFO)
    httpd.serve_forever()

if __name__ == '__main__':
    monitor = xbmc.Monitor()
    http_thread = threading.Thread(target=start_http)
    http_thread.start()
    while not monitor.abortRequested():
        # Sleep/wait for abort for 10 seconds
        if monitor.waitForAbort(10):
            # Abort was requested while waiting. We should exit
            break
