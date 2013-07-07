#!/usr/bin/env python
from wsgiref.simple_server import make_server
import json, socket, subprocess

def cgminer_cmd(m, cmd):
    """
    m : IP
    cmd = dict with command and optionally parameter
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((m, 4028))
    sock.send(bytearray(json.dumps(cmd), 'utf-8'))
    result = ''
    chunk = sock.recv(64)
    while (len(chunk) != 0):
        result = result + str(chunk)
        chunk = sock.recv(64)
    sock.close()
    return result[0:-1]


def get_syslog(lines=20, search=50):
    """
    greps for {lines} lines matching cgminer out of last {search} lines.
    """
    ps = subprocess.Popen(['tail', "-%s" %(search), "/var/log/syslog"], stdout=subprocess.PIPE)
    grep = subprocess.Popen(('grep', 'cgminer'), stdin=ps.stdout, stdout=subprocess.PIPE)
    tail = subprocess.Popen(('tail', "-%s" %(lines)), stdin=grep.stdout, stdout=subprocess.PIPE)
    output, err = tail.communicate()
    return output

def serve_syslog(environ, start_response):
    status = '200 OK'
    content = get_syslog()
    response_headers = [('Content-Type', 'text/html'),
            ('Content-Length', str(len(content)))]
    start_response(status, response_headers)
    return [content]


def api_handler(environ, start_response):
    """
    catches request in format : /api/<command>/<parameter>/
    TODO: Sanitize/validate request/response
    Make RESTful - Enforce PUT/POST for state changing things.
    """
    path = environ['PATH_INFO'].split("/")
    command = {"command": path[2]}
    param = None
    if len(path) > 3:
        if len(path[3]) > 0:
            command["parameter"] = path[3]
    status = '200 OK'
    print path, command
    content = cgminer_cmd("127.0.0.1", command)
    response_headers = [('Content-Type', 'application/json'),
            ('Content-Length', str(len(content)))]
    start_response(status, response_headers)
    return [content]


def application(environ, start_response):
    """
    Anything thats not /api gets served the html file because we will use the location api for things
    """
    if environ['PATH_INFO'].startswith("/api"):
        return api_handler(environ, start_response)
    elif environ['PATH_INFO'].startswith("/syslog"):
        return serve_syslog(environ, start_response)
    else:
        status = '200 OK'
        content = open("static/app.html").read()
        response_headers = [('Content-Type', 'text/html'),
                ('Content-Length', str(len(content)))]
        start_response(status, response_headers)
        return [content]

if __name__ == "__main__":
    #In production probably run application using a real WSGI server -- spawning/gunicorn?
    httpd = make_server('', 1337,  application )
    httpd.serve_forever()
