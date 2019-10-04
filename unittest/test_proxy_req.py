"""

"""
import logging
import time
import re
import asyncio
from multidict import CIMultiDict as MultiDict
from px import ntlm
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
    writer.write(f"CONNECT {remote} HTTP/1.1\r\nHost: {remote}\r\n\r\n".encode())

    await writer.drain()
    log.info("write connect")

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
    log.info(body)

    user = "luosam"
    domain = "FIRMWIDE"
    pwd = "test"
    # ntlm auth -- step 1

    type1_flags = ntlm.NTLM_TYPE1_FLAGS
    # ntlm secures a socket, so we must use the same socket for the complete handshake
    # headers.update(req.unredirected_hdrs)
    auth = b"NTLM " + ntlm.create_NTLM_NEGOTIATE_MESSAGE(user, type1_flags)
    # write connect
    remote = f"{remote_host}:{remote_port}"

    request = (
        f"CONNECT {remote} HTTP/1.1\r\nHost: {remote}\r\n"
        + "User-Agent: Mozilla/4.0 (compatible; MSIE 5.5; Windows 98)\r\n"
        + "Proxy-Connection: Keep-Alive\r\nPragma: no-cache\r\n"
        + "Accept: */*\r\n"
        + f"Proxy-authorization: {auth.decode()}\r\n\r\n"
    )

    log.info("request: \n%s", request)

    writer.write(request.encode())

    await writer.drain()
    # check response

    # if len(user_parts) == 1:
    #     UserName = user_parts[0]
    #     DomainName = ""
    #     type1_flags = ntlm.NTLM_TYPE1_FLAGS & ~ntlm.NTLM_NegotiateOemDomainSupplied
    # else:
    #     DomainName = user_parts[0].upper()
    #     UserName = user_parts[1]
    time.sleep(1)
    log.info("reader: %s, writer: %s", reader, writer)

    while True:

        try:
            headers = await reader.read_until(b"\r\n\r\n")
            if not headers:
                break
            headers = headers.decode()
            assert headers
            print(headers)
            headers = headers.split("\r\n")

            header = headers.pop(0)
            print(header)

        except asyncio.streams.IncompleteReadError:
            pass

    version, code, message = HTTP_RESP_LINE.match(header).groups()

    writer.close()
