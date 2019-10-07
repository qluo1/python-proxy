"""

"""
import base64
import time
import socket
from ntlm_auth.ntlm import Ntlm


def test_http():

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = "asia-proxy-vip.web.gs.com"
    port = 85

    s.connect((host, port))

    request = """CONNECT github.com:443 HTTP/1.1\r\n
Host: github.com:443\r\n
User-Agent: Mozilla/4.0 (compatible; MSIE 5.5; Windows 98)\r\n
\r\n\r\n
"""

    s.sendall(request.encode())

    msg = b""
    while True:
        data = s.recv(64 * 1024)
        msg += data
        if data.endswith(b"\r\n\r\n"):
            msg += data
            break

    print(msg)
    user = "luosam"
    domain = "FIRMWIDE"
    pwd = "test"
    # ntlm auth -- step 1
    context = Ntlm(ntlm_compatibility=0)
    auth = base64.b64encode(context.create_negotiate_message(domain))
    #
    request = f"""CONNECT github.com:443 HTTP/1.1\r\n
Host: github.com:443\r\n
User-Agent: Mozilla/4.0 (compatible; MSIE 5.5; Windows 98)\r\n
Proxy-Connection: Keep-Alive\r\n
Proxy-Authorization: NTLM {auth}\r\n
\r\n\r\n
"""
    s.sendall(request.encode())
    time.sleep(1)

    msg = b""
    while True:
        data = s.recv(64 * 1024)
        if data:
            msg += data
            if data.endswith(b"\r\n\r\n"):
                msg += data
                break
        else:
            break

    print(msg)
