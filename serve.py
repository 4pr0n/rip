import CGIHTTPServer

import BaseHTTPServer

class Handler(CGIHTTPServer.CGIHTTPRequestHandler):
    cgi_extensions = ["cgi", "py"]
    # don't really need PY

PORT = 8000


from SocketServer import ThreadingMixIn
import threading


class ThreadedHTTPServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
    """Handle requests in a separate thread."""

if __name__ == '__main__':
	httpd = ThreadedHTTPServer(("", PORT), Handler)
        print 'Starting server, use <Ctrl-C> to stop'
	print "serving at port", PORT
	httpd.serve_forever()
