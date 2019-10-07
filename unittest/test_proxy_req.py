"""

"""
import logging
import time
import socket
import re
import base64
import asyncio
from multidict import CIMultiDict as MultiDict
from ntlm_auth.ntlm import NtlmContext
import pytest


log = logging.getLogger("test")
loop = asyncio.get_event_loop()
loop.set_debug(True)


asyncio.StreamReader.read_until = lambda self, s: asyncio.wait_for(
    self.readuntil(s), timeout=300
)
asyncio.StreamReader.read_n = lambda self, n: asyncio.wait_for(
    self.readexactly(n), timeout=300
)

HTTP_RESP_LINE = re.compile(r"^(HTTP/[^ ]+) +(\d+?) +(.+?)$")


@pytest.mark.asyncio
async def test_connect():

    remote_host = "github.com"
    remote_port = 443
    host = "asia-proxy-vip.web.gs.com"
    port = 85
    reader, writer = await asyncio.open_connection(host, port)

    # write connect
    remote = f"{remote_host}:{remote_port}"
    req = (
        f"CONNECT {remote} HTTP/1.1\r\nHost: {remote}\r\n"
        + "User-Agent: Mozilla/4.0 (compatible; MSIE 5.5; Windows 98)\r\n"
        + "Accept: image/gif, image/x-xbitmap, image/jpeg, image/pjpeg, application/vnd.ms-excel, application/msword, application/vnd.ms-powerpoint, */*"
        + "Proxy-Connection: Keep-Alive\r\n\r\n"
    ).encode()
    log.info("req: %s", req)
    writer.write(req)

    await writer.drain()
    log.info("write connect done")

    headers = await reader.read_until(b"\r\n\r\n")
    headers = headers.decode()
    assert headers
    log.info(headers)

    headers = headers.split("\r\n")

    header = headers.pop(0)
    print(header)
    log.info(header)

    version, code, message = HTTP_RESP_LINE.match(header).groups()

    assert int(code) == 407
    assert message == "Proxy Authentication Required"
    reqs = MultiDict()
    for k, v in [ln.split(":", 1) for ln in headers if ln]:
        reqs.add(k.strip(), v.strip())
    print(reqs)

    assert reqs.getall("Proxy-Authenticate") == ["NEGOTIATE", "NTLM"]

    body_length = int(reqs["Content-Length"])

    body = await reader.read_n(body_length)
    # log.info(body)

    user = "luosam"
    domain = "FIRMWIDE"
    pwd = "test"
    context = NtlmContext(user, pwd, domain=domain, workstation=socket.gethostname())
    # ntlm auth -- step 1
    auth = base64.b64encode(context.step())
    # write connect
    remote = f"{remote_host}:{remote_port}"
    request = (
        f"CONNECT {remote} HTTP/1.1\r\nHost: {remote}\r\n"
        + "User-Agent: Mozilla/4.0 (compatible; MSIE 5.5; Windows 98)\r\n"
        + "Proxy-Connection: Keep-Alive\r\n"
        + "Accept: */*\r\n"
        + f"Proxy-Authorization: NTLM {auth.decode()}\r\n\r\n"
    )

    log.info("request: \n%s", request)

    writer.write(request.encode())
    await writer.drain()

    # check response
    time.sleep(1)
    log.info("reader: %s, writer: %s", reader, writer)

    headers = await reader.read_until(b"\r\n\r\n")
    headers = headers.decode()
    assert headers
    print(headers)
    headers = headers.split("\r\n")

    header = headers.pop(0)
    print(header)

    version, code, message = HTTP_RESP_LINE.match(header).groups()

    writer.close()
