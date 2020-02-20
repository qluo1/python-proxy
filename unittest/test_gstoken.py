import requests
from requests_kerberos import HTTPKerberosAuth


def test_token():
    # self.token =
    auth = HTTPKerberosAuth()
    req_session = requests.session()
    req_session.get(
        "https://authn.web.gs.com/desktopsso/Login", auth=auth, verify=True
    ).raise_for_status()
    assert req_session.cookies
    assert "GSSSO" in req_session.cookies
