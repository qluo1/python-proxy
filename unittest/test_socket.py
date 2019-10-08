"""

"""
import re
import os
import logging
import base64
import time
import socket
from ntlm_auth.ntlm import NtlmContext
from multidict import CIMultiDict as MultiDict


def get_response(sock):
    msg = b""
    while True:
        data = sock.recv(8 * 1024)
        print(data)
        if not data:
            break
        msg += data
        if data.endswith(b"\r\n\r\n"):
            break
    return msg


def parse_response_headers(response):

    header, _ = response.split("\r\n\r\n", 1)

    lines = header.split("\r\n")
    headers = MultiDict()
    for ln in lines[1:]:
        k, v = ln.split(":", 1)
        headers.add(k, v)

    return headers


def test_http():
    host = "asia-proxy-vip.web.gs.com"
    port = 85
    s = socket.create_connection((host, port))
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    pwd = os.environ.get("NTLM_PWD")
    assert pwd
    context = NtlmContext(
        "luosam", pwd, domain="FIRMWIDE", workstation=socket.gethostname()
    )
    # step 1
    request = f"CONNECT github.com:443 HTTP/1.1\r\nAccept-Encoding: identity\r\nHost: github.com:443\r\nUser-Agent: Mozilla/4.0 (compatible; MSIE 5.5; Windows 98)\r\nProxy-Connection: Keep-Alive\r\nProxy-Authorization: NTLM {base64.b64encode(context.step()).decode()}\r\n\r\n"
    print("send: ", request)
    s.sendall(request.encode())

    msg = get_response(s)
    headers = parse_response_headers(msg.decode())
    token = headers["Proxy-Authenticate"]
    print("reply: ", msg)
    logging.info("resp: %s", msg)
    # assert msg
    request = f"CONNECT github.com:443 HTTP/1.1\r\nAccept-Encoding: identity\r\nHost: github.com:443\r\nUser-Agent: Mozilla/4.0 (compatible; MSIE 5.5; Windows 98)\r\nProxy-Connection: Keep-Alive\r\nProxy-Authorization: NTLM {base64.b64encode(context.step(base64.b64decode(token[5:].encode()))).decode()}\r\n\r\n"
    print("send {}".format(request))
    s.sendall(request.encode())
    msg = get_response(s)
    print("reply: {}".format(msg))

    s.close()
