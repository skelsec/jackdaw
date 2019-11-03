
from flask import send_file, send_from_directory

def serve_file(filename):
    response = send_from_directory('static', filename)
    response.direct_passthrough = False
    return response

def serve_home():
    filename = 'test.html'
    response = send_from_directory('static', filename)
    response.direct_passthrough = False
    return response