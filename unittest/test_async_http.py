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


async def read_response(reader):
    # read response
    headers = await reader.read_until(b"\r\n\r\n")
    headers = headers.decode()
    assert headers
    log.info(headers)

    headers = headers.split("\r\n")

    header = headers.pop(0)
    print(header)
    log.info(header)

    version, code, message = HTTP_RESP_LINE.match(header).groups()

    assert message == "Proxy Authentication Required"
    reqs = MultiDict()
    for k, v in [ln.split(":", 1) for ln in headers if ln]:
        reqs.add(k.strip(), v.strip())
    assert reqs.getall("Proxy-Authenticate") == ["NEGOTIATE", "NTLM"]
    body_length = int(reqs["Content-Length"])
    body = await reader.read_n(body_length)
    body = body.decode()
    body = body.split("\r\n")
    # for ln in body:
    #     log.debug(ln)

    return int(code), reqs


@pytest.mark.asyncio
async def test_proxy_connect():

    host = "asia-proxy-vip.web.gs.com"
    port = 85
    reader, writer = await asyncio.open_connection(host, port)

    writer.write(
        b"CONNECT github.com:443 HTTP/1.1\r\nAccept-Encoding: identity\r\nHost: github.com:443\r\nUser-Agent: Mozilla/4.0 (compatible; MSIE 5.5; Windows 98)\r\nProxy-Connection: Keep-Alive\r\n\r\n"
    )
    await writer.drain()

    # read response
    status, headers = await read_response(reader)
    assert status == 407
    log.info("headers: %s", headers)

    # step 1
    writer.write(
        b"CONNECT github.com:443 HTTP/1.1\r\nAccept-Encoding: identity\r\nHost: github.com:443\r\nUser-Agent: Mozilla/4.0 (compatible; MSIE 5.5; Windows 98)\r\nProxy-Connection: Keep-Alive\r\nProxy-Authorization: NTLM TlRMTVNTUAABAAAAMrCI4ggACAAoAAAAFQAVADAAAAAGAbEdAAAAD0ZJUk1XSURFZDM0MDk3OS0wMDYuZGMuZ3MuY29t\r\n\r\n"
    )
    await writer.drain()

    data = await reader.read()
    print(data)

    # read response
    status, headers = await read_response(reader)
    log.info("headers: %s", headers)
    assert status == 407
