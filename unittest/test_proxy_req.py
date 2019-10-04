"""

"""
import re
import asyncio
from multidict import CIMultiDict as MultiDict
from px import ntlm
import pytest

asyncio.StreamReader.read_until = lambda self, s: asyncio.wait_for(
    self.readuntil(s), timeout=300
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

    headers = await reader.read_until(b"\r\n\r\n")
    headers = headers.decode()
    assert headers
    print(headers)

    headers = headers.split("\r\n")

    header = headers.pop(0)
    print(header)

    version, code, message = HTTP_RESP_LINE.match(header).groups()

    assert int(code) == 407
    assert message == "Proxy Authentication Required"
    reqs = MultiDict()
    for k, v in [ln.split(":", 1) for ln in headers if ln]:
        reqs.add(k.strip(), v.strip())
    print(reqs)

    assert reqs.getall("Proxy-Authenticate") == ["NEGOTIATE", "NTLM"]

    # ntlm auth
    reqs["Connection"] = "Keep-Alive"

    user = "luosam"
    domain = "FIRMWIDE"
    pwd = "test"
    # if len(user_parts) == 1:
    #     UserName = user_parts[0]
    #     DomainName = ""
    #     type1_flags = ntlm.NTLM_TYPE1_FLAGS & ~ntlm.NTLM_NegotiateOemDomainSupplied
    # else:
    #     DomainName = user_parts[0].upper()
    #     UserName = user_parts[1]

    type1_flags = ntlm.NTLM_TYPE1_FLAGS
    # ntlm secures a socket, so we must use the same socket for the complete handshake
    # headers.update(req.unredirected_hdrs)
    auth = "NTLM %s" % ntlm.create_NTLM_NEGOTIATE_MESSAGE(user, type1_flags)
    reqs["Proxy-Authenticate"] = auth
    print(reqs)

    # write response

    writer.close()
