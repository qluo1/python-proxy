"""

"""
import re
import urllib.parse
import logging
import binascii
import asyncio
from asyncio import StreamReader, StreamWriter
import socket

# import hexdump

SOCKET_TIMEOUT = 300
PACKET_SIZE = 65536

EOD_HTTP_REQ = b"\r\n\r\n"


# help for stream reader
asyncio.StreamReader.read_ = lambda self: self.read(PACKET_SIZE)
asyncio.StreamReader.read_n = lambda self, n: asyncio.wait_for(
    self.readexactly(n), timeout=SOCKET_TIMEOUT
)
asyncio.StreamReader.read_until = lambda self, s: asyncio.wait_for(
    self.readuntil(s), timeout=SOCKET_TIMEOUT
)

HTTP_LINE = re.compile("([^ ]+) +(.+?) +(HTTP/[^ ]+)$")
HTTP_RESP_LINE = re.compile("^(HTTP/[^ ]+) +(\d+?) +(.+?)$")

# packstr = lambda s, n=1: len(s).to_bytes(n, "big") + s

log = logging.getLogger(__name__)


async def parse_http_request_header(reader: StreamReader, writer: StreamWriter):
    """ parsing client initial HTTP request header

    return target host/port request message

    """
    lines = await reader.read_until(b"\r\n\r\n")
    headers = lines[:-1].decode().split("\r\n")
    method, path, ver = HTTP_LINE.match(headers.pop(0)).groups()
    log.info("original req: %s", lines)
    url = urllib.parse.urlparse(path)
    #
    lines = "\r\n".join(i for i in headers if not i.startswith("Proxy-") and i.strip())
    headers = dict(i.split(": ", 1) for i in headers if ": " in i)

    if method == "CONNECT":
        host_name, port = path.split(":", 1)
        port = int(port)
        writer.write(f"{ver} 200 OK\r\n Connection: close\r\n\r\n".encode())
        return host_name, port, b""

    else:
        url = urllib.parse.urlparse(path)
        host_name = url.hostname
        port = url.port or 80
        newpath = url._replace(netloc="", scheme="").geturl()

        req = f"{method} {newpath} {ver}\r\n{lines}\r\n\r\n".encode()
        log.debug("new req: %s", req)
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
            if b"\r\n" in data and HTTP_LINE.match(data.split(b"\r\n", 1)[0].decode()):
                if b"\r\n\r\n" not in data:
                    data += await reader.readuntil(b"\r\n\r\n")

                lines, data = data.split(b"\r\n\r\n", 1)
                headers = lines[:-1].decode().split("\r\n")
                method, path, ver = HTTP_LINE.match(headers.pop(0)).groups()

                # remove proxy
                lines = "\r\n".join(
                    i for i in headers if not i.startswith("Proxy-") and i.strip()
                )

                headers = dict(i.split(": ", 1) for i in headers if ": " in i)
                newpath = (
                    urllib.parse.urlparse(path)._replace(netloc="", scheme="").geturl()
                )
                data = f"{method} {newpath} {ver}\r\n{lines}\r\n\r\n".encode() + data

            writer.write(data)
            await writer.drain()

    except Exception as ex:
        log.exception(ex)
    finally:
        writer.close()


async def test_ssl_handshake(reader, writer, remote_reader, remote_writer):
    """

    """

    while True:
        try:

            data = await reader.read_()
            if not data:
                log.warning("<-- EOF: %s", reader.at_eof())
                break
            log.info("<-- \n%s", binascii.b2a_hex(data))

            remote_writer.write(data)
            await remote_writer.drain()

            resp = await remote_reader.read_()
            if not resp:
                log.warning("<-- EOF: %s", remote_reader.at_eof())
                break
            log.info("--> \n%s", binascii.b2a_hex(resp))

            writer.write(resp)
            await writer.drain()

        except Exception as e:
            log.exception(e)
            break
        finally:
            remote_writer.close()
            writer.close()


class Proxy(object):
    """

    """

    def __init__(self, settings):
        """ """

        self.settings = settings

        self.proxies = []

        for proxy in settings.parent_proxy:
            self.proxies.append((proxy, settings.parent_proxy_port))

    async def get_parent_proxy(self, remote_host, remote_port):

        for proxy in self.proxies:

            try:
                reader, writer = await asyncio.open_connection(*proxy)
                # authenticate
                remote = f"{remote_host}:{remote_port}"
                writer.write(
                    f"CONNECT {remote} HTTP/1.1\r\nHost: {remote}\r\n\r\n".encode()
                )

                await writer.drain()

                lines = await reader.read_until(b"\r\n\r\n")
                headers = lines[:-1].decode().split("\r\n")
                version, code, message = HTTP_RESP_LINE.match(headers.pop(0)).groups()
                log.info("proxy response: %s", lines)
                # prepare ntll auth
                if (
                    code == "407"
                    and message == "Proxy Authentication Required"
                    and "Proxy-Authenticate" in lines
                    and "NTLM" in lines
                ):
                    pass

                # proxy ready to be used
                return reader, writer

            except Exception as e:
                log.exception(e)
                writer.close()

            raise ValueError("no proxy available")

    async def handle_client(self, reader: StreamReader, writer: StreamWriter):
        """ handle incoming clent session

        """
        peername = writer.transport.get_extra_info("peername")
        log.info("handle_client : %s", peername)

        try:

            remote_host, remote_port, req = await parse_http_request_header(
                reader, writer
            )
            # check dns
            try:
                socket.gethostbyname(remote_host)

                remote_reader, remote_writer = await asyncio.open_connection(
                    remote_host, remote_port
                )

            except socket.gaierror:
                # must via internal proxy
                remote_reader, remote_writer = await self.get_parent_proxy(
                    remote_host, remote_port
                )

            # write
            remote_writer.write(req)
            asyncio.create_task(http_channel(reader, remote_writer))
            asyncio.create_task(http_channel(remote_reader, writer))

        except Exception as ex:
            log.exception(ex)
