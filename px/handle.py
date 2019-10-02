"""

"""
import re
import urllib.parse
import logging
import binascii
import hexdump
import asyncio
from asyncio import StreamReader, StreamWriter

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
# packstr = lambda s, n=1: len(s).to_bytes(n, "big") + s

log = logging.getLogger(__name__)


async def parse_http_request_header(reader: StreamReader, writer: StreamWriter):
    """ parsing client initial HTTP request header

    return target host/port request message

    """

    lines = await reader.read_until(b"\r\n\r\n")
    headers = lines[:-1].decode().split("\r\n")
    method, path, ver = HTTP_LINE.match(headers.pop(0)).groups()
    log.info("req original: %s", lines)
    url = urllib.parse.urlparse(path)
    #
    lines = "\r\n".join(i for i in headers if not i.startswith("Proxy-") and i.strip())
    headers = dict(i.split(": ", 1) for i in headers if ": " in i)

    if method == "CONNECT":
        host_name, port = path.split(":", 1)
        port = int(port)
        writer.write(f"{ver} 200 OK\r\n Proxy-Connection: Keep-Alive\r\n\r\n".encode())
        return host_name, port, b""

    else:
        url = urllib.parse.urlparse(path)
        host_name = url.hostname
        port = url.port or 80
        newpath = url._replace(netloc="", scheme="").geturl()

        req = f"{method} {newpath} {ver}\r\n{lines}\r\n\r\n".encode()
        log.info("new req: %s", req)
        return (host_name, port, req)


async def channel(reader: StreamReader, writer: StreamWriter):
    """ channel reader to writer """
    # channel HTTP reader to writer
    peername = writer.transport.get_extra_info("peername")
    while True:

        try:
            log.debug("channel reading for %s", peername)
            data = await reader.read_()
            if not data:
                log.warning("no data: EOF: %s, to: %s", reader.at_eof(), peername)
                break
            log.debug("to %s, data:\n%s", peername, binascii.hexlify(data))
            hexdump.hexdump(data)
            writer.write(data)
            await writer.drain()
            log.info("done write to %s", peername)

        except Exception as ex:
            log.info("lost client session [%s] due to [%s]", peername, ex)
            log.exception(ex)
            # end session
            return
        finally:
            writer.close()


async def http_channel(reader: StreamReader, writer: StreamWriter):
    """ channel HTTP reader to writer

    """
    # channel HTTP reader to writer
    peername = writer.transport.get_extra_info("peername")
    log.info("channel to :%s", peername)
    while True:

        try:

            data = await reader.read_()
            if not data:
                log.warning("no data: EOF: %s, to: %s", reader.at_eof(), peername)
                break

            log.info("to %s, data:\n%s", peername, binascii.hexlify(data))
            # http header
            if b"\r\n" in data and HTTP_LINE.match(data.split(b"\r\n", 1)[0].decode()):
                log.info("http header found")
                if b"\r\n\r\n" not in data:
                    data += await reader.readuntil(b"\r\n\r\n")

                lines, data = data.split(b"\r\n\r\n", 1)
                headers = lines[:-1].decode().split("\r\n")
                log.info("to %s, header %s", peername, headers)
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
            log.info("done write to %s", peername)

        except Exception as ex:
            log.info("lost client session [%s] due to [%s]", peername, ex)
            log.exception(ex)
            # end session
            return
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

        self.running = True

    async def handle_client(self, reader: StreamReader, writer: StreamWriter):
        """ handle incoming clent session

        """
        peername = writer.transport.get_extra_info("peername")
        log.info("handle_client : %s", peername)
        loop = asyncio.get_event_loop()

        try:

            remote_host, remote_port, req = await parse_http_request_header(
                reader, writer
            )

            remote_reader, remote_writer = await asyncio.open_connection(
                remote_host, remote_port
            )
            if req:
                log.info("req: %s", req)
                remote_writer.write(req)

            # task1 = asyncio.create_task(http_channel(reader, remote_writer))
            # task2 = asyncio.create_task(http_channel(remote_reader, writer))

            # await task1
            # await task2

            # while True:
            #     if task1.done() and task2.done():
            #         break

            #     await asyncio.sleep(1)

            # await test_ssl_handshake(reader, writer, remote_reader, remote_writer)
            loop.create_task(channel(remote_reader, writer))
            loop.create_task(channel(reader, remote_writer))

        except Exception as ex:
            log.exception(ex)

        log.info("handle_client ended")
