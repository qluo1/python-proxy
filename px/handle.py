"""

"""
import re
import urllib.parse
import logging
import asyncio
from asyncio import StreamReader, StreamWriter
import socket
import base64
import getpass
from ntlm_auth.ntlm import NtlmContext
from multidict import CIMultiDict as MultiDict
import requests
from requests_kerberos import HTTPKerberosAuth
from .gssso import get_gssso, AuthFailed

SOCKET_TIMEOUT = 300
PACKET_SIZE = 2 ** 16  # 64K


# help for stream reader
asyncio.StreamReader.read_ = lambda self: self.read(PACKET_SIZE)
asyncio.StreamReader.read_n = lambda self, n: asyncio.wait_for(
    self.readexactly(n), timeout=SOCKET_TIMEOUT
)
asyncio.StreamReader.read_until = lambda self, s: asyncio.wait_for(
    self.readuntil(s), timeout=SOCKET_TIMEOUT
)

HTTP_LINE = re.compile(r"([^ ]+) +(.+?) +(HTTP/[^ ]+)$")
HTTP_RESP_LINE = re.compile(r"^(HTTP/[^ ]+) +(\d+?) +(.+?)$")


log = logging.getLogger(__name__)


async def parse_http_request_header(reader: StreamReader, writer: StreamWriter):
    """ parsing client initial HTTP request header

    return target host/port request message

    """
    lines = await reader.read_until(b"\r\n\r\n")
    headers = lines[:-1].decode().split("\r\n")
    method, path, ver = HTTP_LINE.match(headers.pop(0)).groups()
    log.debug("original req: %s", lines)
    url = urllib.parse.urlparse(path)
    #
    lines = "\r\n".join(i for i in headers if not i.startswith("Proxy-") and i.strip())
    headers = dict(i.split(": ", 1) for i in headers if ": " in i)

    if method == "CONNECT":
        host_name, port = path.split(":", 1)
        log.info("connect :%s %s", host_name, port)
        port = int(port)
        writer.write(f"{ver} 200 OK\r\n Connection: close\r\n\r\n".encode())
        return host_name, port, b""

    else:
        url = urllib.parse.urlparse(path)
        host_name = url.hostname
        port = url.port or 80
        newpath = url._replace(netloc="", scheme="").geturl()
        req = f"{method} {newpath} {ver}\r\n{lines}\r\n\r\n".encode()

        try:
            # gs host set cookie
            socket.gethostbyname(host_name)
            # set cookie for internal host
            try:
                cookie = get_gssso()
                log.debug("set cookie: %s", cookie)
                if method.upper() in ("GET", "POST") and cookie:
                    req = f"{method} {newpath} {ver}\r\n{lines}\r\nCookie:{cookie}\r\n\r\n".encode()

            except AuthFailed:
                pass

        except Exception as ex:
            log.info("external site :%s", ex)

        log.info("new req: %s:%s %s", host_name, port, req)
        return (host_name, port, req)


async def http_channel(reader: StreamReader, writer: StreamWriter):
    """ channel HTTP reader to writer

    """
    # channel HTTP reader to writer
    peername = writer.transport.get_extra_info("peername")
    try:
        while True:
            data = await reader.read_()
            if not data:
                log.debug("no data: EOF: %s, to: %s", reader.at_eof(), peername)
                break

            # http header
            if b"\r\n" in data and HTTP_LINE.match(
                data.split(b"\r\n", 1)[0].decode("utf8", "ignore")
            ):
                if b"\r\n\r\n" not in data:
                    data += await reader.readuntil(b"\r\n\r\n")

                lines, data = data.split(b"\r\n\r\n", 1)
                headers = lines[:-1].decode().split("\r\n")
                method, path, ver = HTTP_LINE.match(headers.pop(0)).groups()

                # set cookie
                if method.upper() in ("GET", "POST"):
                    try:
                        cookie = get_gssso()
                        headers.append(f"Cookie:{cookie}")
                    except AuthFailed:
                        pass

                # remove proxy
                lines = "\r\n".join(
                    i for i in headers if not i.startswith("Proxy-") and i.strip()
                )

                newpath = (
                    urllib.parse.urlparse(path)._replace(netloc="", scheme="").geturl()
                )
                header = f"{method} {newpath} {ver}\r\n{lines}\r\n\r\n"
                data = header.encode() + data
                log.info("write http header : %s", header)

            # log.debug("write data: %s", data)
            writer.write(data)
            await writer.drain()

    except Exception as ex:
        log.exception(ex)
    finally:
        writer.close()


class Proxy(object):
    """

    """

    def __init__(self, settings):
        """ """
        self.settings = settings
        self.ntlm_proxy = settings.ntlm_proxy
        self.ntlm_user = settings.ntlm_proxy_user or getpass.getuser()
        self.ntlm_domain = settings.ntlm_proxy_domain
        self.ntlm_pwd = base64.b64decode(settings.ntlm_proxy_pwd).decode()

    async def proxy_auth_ntml(self, remote_host, remote_port):
        """ ntlm auth """

        context = NtlmContext(
            self.ntlm_user,
            self.ntlm_pwd,
            domain=self.ntlm_domain,
            workstation=socket.gethostname(),
        )
        reader, writer = await asyncio.open_connection(*self.ntlm_proxy)
        # write connect
        remote = f"{remote_host}:{remote_port}"
        req = (
            f"CONNECT {remote} HTTP/1.1\r\nHost: {remote}\r\n"
            + "User-Agent: Mozilla/4.0 (compatible; MSIE 5.5; Windows 98)\r\n"
            + "Accept: */*\r\n"
            + "Proxy-Connection: Keep-Alive\r\n"
            + f"Proxy-Authorization: NTLM {base64.b64encode(context.step()).decode()}\r\n\r\n"
        ).encode()
        log.debug("req: %s", req)
        writer.write(req)
        await writer.drain()

        headers = await reader.read_until(b"\r\n\r\n")
        headers = headers.decode()
        assert headers
        log.debug(headers)

        headers = headers.split("\r\n")
        header = headers.pop(0)

        version, code, message = HTTP_RESP_LINE.match(header).groups()

        assert int(code) == 407
        assert message == "Proxy Authentication Required"
        reqs = MultiDict()
        for k, v in [ln.split(":", 1) for ln in headers if ln]:
            reqs.add(k.strip(), v.strip())

        token = reqs.get("Proxy-Authenticate")
        assert token

        body_length = int(reqs["Content-Length"])
        body = await reader.read_n(body_length)
        log.debug(body)

        # write connect
        remote = f"{remote_host}:{remote_port}"
        request = (
            f"CONNECT {remote} HTTP/1.1\r\nHost: {remote}\r\n"
            + "User-Agent: Mozilla/4.0 (compatible; MSIE 5.5; Windows 98)\r\n"
            + "Proxy-Connection: Keep-Alive\r\n"
            + "Accept: */*\r\n"
            + f"Proxy-Authorization: NTLM {base64.b64encode(context.step(base64.b64decode(token[5:].encode()))).decode()}\r\n\r\n"
        )
        log.info("request: \n%s", request)

        writer.write(request.encode())
        await writer.drain()

        headers = await reader.read_until(b"\r\n\r\n")
        headers = headers.decode()
        headers = headers.split("\r\n")
        header = headers.pop(0)
        log.info(header)
        version, code, message = HTTP_RESP_LINE.match(header).groups()
        if int(code) == 200:
            return reader, writer
        else:
            raise ValueError(f"auth failed: {header} \n {headers}")

    async def handle_client(self, reader: StreamReader, writer: StreamWriter):
        """ handle incoming clent session

        """
        peername = writer.transport.get_extra_info("peername")
        log.info("handle_client : %s", peername)

        try:

            remote_host, remote_port, req = await parse_http_request_header(
                reader, writer
            )

            # check dns if unknown using proxy for external host
            try:
                socket.gethostbyname(remote_host)

                remote_reader, remote_writer = await asyncio.open_connection(
                    remote_host, remote_port
                )

                # internal
            except socket.gaierror:
                # must via internal proxy
                remote_reader, remote_writer = await self.proxy_auth_ntml(
                    remote_host, remote_port
                )

            # write
            remote_writer.write(req)
            asyncio.create_task(http_channel(reader, remote_writer))
            asyncio.create_task(http_channel(remote_reader, writer))
        except Exception as ex:
            log.exception(ex)
