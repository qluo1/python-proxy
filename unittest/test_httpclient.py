import os
import sys
import logging
import http.client
import socket
import base64
from ntlm_auth.ntlm import NtlmContext


# HTTP stream handler
class WritableObject:
    def write(self, string):
        if string.strip():
            logging.info(string)

    def flush(self):
        pass


sys.stdout = WritableObject()


def test_urllib3():
    """ """
    host = "asia-proxy-vip.web.gs.com"
    port = 85

    conn = http.client.HTTPConnection(host, port)
    conn.set_debuglevel(1)

    headers = {
        "Host": "github.com:443",
        "User-Agent": "Mozilla/4.0 (compatible; MSIE 5.5; Windows 98)",
        "Proxy-Connection": "Keep-Alive",
    }
    conn.request("CONNECT", "github.com:443", headers=headers)

    resp = conn.getresponse()
    assert resp.status == 407
    # print(resp)
    print(resp.headers.items())
    body = resp.read()
    pwd = os.environ.get("NTLM_PWD")
    assert pwd, "please supply NTLM_PWD as envrionment variable"

    context = NtlmContext(
        "luosam", pwd, domain="FIRMWIDE", workstation=socket.gethostname()
    )
    headers["Proxy-Authorization"] = "NTLM " + base64.b64encode(context.step()).decode()
    conn.request("CONNECT", "github.com:443", headers=headers)

    resp = conn.getresponse()
    print(resp)
    print(resp.headers.items())

    body = resp.read()
    logging.debug(body)
    assert resp.status == 407

    token = resp.headers["Proxy-Authenticate"]
    headers["Proxy-Authorization"] = (
        "NTLM "
        + base64.b64encode(context.step(base64.b64decode(token[5:].encode()))).decode()
    )

    conn.request("CONNECT", "github.com:443", headers=headers)
    resp = conn.getresponse()
    print(resp)
    print(resp.headers.items())

    assert resp.status == 200

    conn.close()
