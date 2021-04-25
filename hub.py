#!/usr/bin/env python
# -*- coding: utf-8 -*
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from json import loads
from os import getenv
from sys import argv
from requests import session

from matrix_client.client import MatrixClient
from matrix_client.errors import MatrixHttpLibError

from settings import (
    ONION_ADDR,
    LOG_USER,
    LOG_PASSWORD
)


logging.basicConfig(level=logging.INFO)


class HiddenService:
    session = requests.session()
    proxies = {
        'http': 'socks5h://localhost:9050',
        'https': 'socks5h://localhost:9050'
    }

    def __init__(self, *args, **kwargs):
        self.session.proxies = self.proxies
        self.addrs = addrs

    def put(self, id_device, json_data):
        self.url = "http://{self.addrs['id_device']}"
        session_obj = self.session.put(self.url, json=json_data)
        if session_obj.ok:
            logging.success(json_data)
        else:
            logging.error(f"failed to connect {URL}")


class Logger:
    address: str
    port: int
    token: str
    rooms: dict

    def __init__(self, *args, **kwargs):
        self.address, self.port = args[0]
        if 'username' not in kwargs:
            kwargs.update({'username': LOG_USER})
        if 'password' not in kwargs:
            kwargs.update({'password': LOG_PASSWORD})
        try:
            self._client = MatrixClient(f"http://{self.address}:{self.port}")
            self.token = self._client.login(**kwargs)
        except MatrixHttpLibError as matrix_error:
            logging.error(matrix_error)

    def log(self, room_name, message):
        if not self.token:
            logging.error(f"MatrixClient was not properly intialized. No log can be done")
            return
        if room not in self.rooms:
            logger.info(f"Adding new {room} room to logger")
            room = self._client.join_room(room)
            # TODO: get actual room name
            room_name = 'test_room'
            self.rooms[room_name] = room
        logger.info(f"Sending {message} to {room}")
        self.rooms[room_name].send_text(message)


class ProxyHandler(BaseHTTPRequestHandler):
    logger: Logger
    hidden_service: HiddenService

    def __init__(self, *args, **kwargs):
        self.logger = Logger(args[1])
        self.hidden_service = HiddenService(ONION_ADDR)
        super().__init__(*args, **kwargs)

    def _send_response(self, code=200):
        self.send_response(code)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"")

    def do_PUT(self):
        content_length = int(self.headers["Content-Length"])
        put_data = self.rfile.read(content_length).decode("utf-8")
        logging.info(
            f"PUT request was:\n\
            Path: {self.path}\n\
            Headers: {self.headers}\
            Body: {put_data}"
        )
        device_data = loads(put_data)
        id_device = device_data["device_id"]
        to_send = device_data["data"]
        self.hidden_service.put(id_device, to_send)
        self.logger.log(id_device, to_send)
        self._send_response()

    def do_GET(self):
        content_length = int(self.headers["Content-Length"])
        self._send_response()

    def send_error(self, *args, **kwargs):
        self._send_response(400)


def run(server_class=HTTPServer, handler_class=ProxyHandler, port=8000):
    httpd = server_class(("", port), handler_class)
    try: httpd.serve_forever()
    except KeyboardInterrupt:
        print("Stopping server execution")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    print("Starting server execution")
    if len(argv) > 1:
        port = int(argv[1])
        run(port=int(port))
    else:
        run()