
from flask import send_file, send_from_directory

def serve_file(filename):
    response = send_from_directory('site/nui/dist', filename)
    response.direct_passthrough = False
    return response

def serve_index():
    response = send_from_directory('site/nui/dist', 'index.html')
    response.direct_passthrough = False
    return response

def serve_favico():
    response = send_from_directory('site/static/img', 'favicon.ico')
    response.direct_passthrough = False
    return response
