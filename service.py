import xbmc
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

class VoxHTTPHandler(BaseHTTPRequestHandler):
    def _prep_resp(self, url, write_content: bool):
        resp = requests.get(url)
        resp.raise_for_status()
        self.send_response(int(resp.status_code))
        headers = resp.headers
        for header_name in headers.keys():
            self.send_header(header_name, headers[header_name])
        self.end_headers()
        if write_content:
            self.wfile.write(resp.content)

    def do_GET(self):
        artwork_url = self.path[1:]
        xbmc.log(f"GET path is: {artwork_url}", xbmc.LOGINFO)
        self._prep_resp(artwork_url, True)
        
    def do_HEAD(self):
        artwork_url = self.path[1:]
        xbmc.log(f"HEAD path is: {artwork_url}", xbmc.LOGINFO)
        self._prep_resp(artwork_url, False)

def start_http():
    server_address = ('localhost', 59876)
    httpd = HTTPServer(server_address, VoxHTTPHandler)
    xbmc.log(f"starting http server on localhost pot 59876", xbmc.LOGINFO)
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
