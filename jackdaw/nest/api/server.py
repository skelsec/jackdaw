
from flask import send_file, send_from_directory

def serve_file(filename):
    response = send_from_directory('site', filename)
    response.direct_passthrough = False
    return response

def serve_favico():
    response = send_from_directory('site/static/img', 'favicon.ico')
    response.direct_passthrough = False
    return response

def serve_js(filename):
    response = send_from_directory('site/static/js', filename)
    response.direct_passthrough = False
    return response

def serve_css(filename):
    response = send_from_directory('site/static/css', filename)
    response.direct_passthrough = False
    return response

def serve_img(filename):
    response = send_from_directory('site/static/img', filename)
    response.direct_passthrough = False
    return response

def serve_home():
    response = send_from_directory('site/templates', 'index.html')
    response.direct_passthrough = False
    return response