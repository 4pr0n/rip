import CGIHTTPServer

import BaseHTTPServer

class Handler(CGIHTTPServer.CGIHTTPRequestHandler):

    # cgi_directories = ["/rip"]
    # cgi_extensions = ["py", "cgi"]
    cgi_extensions = ["cgi", "py"]

PORT = 8000


from SocketServer import ThreadingMixIn
import threading


class ThreadedHTTPServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
    """Handle requests in a separate thread."""

if __name__ == '__main__':
    # server = ThreadedHTTPServer(('localhost', 8080), Handler)
    # print 'Starting server, use <Ctrl-C> to stop'
    # server.serve_forever()

	# httpd = BaseHTTPServer.HTTPServer(("", PORT), Handler)
	httpd = ThreadedHTTPServer(("", PORT), Handler)
	print "serving at port", PORT
	httpd.serve_forever()
