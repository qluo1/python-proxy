import urllib.request as urllib2
from px.ntlmauth import HTTPNtlmAuthHandler


def test_one():
    url = "http://asia-proxy-vip.web.gs.com:85/securedfile.html"
    user = u"FIRMWIDE\\luosam"
    password = "Password"

    passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, url, user, password)
    # auth_basic = urllib2.HTTPBasicAuthHandler(passman)
    # auth_digest = urllib2.HTTPDigestAuthHandler(passman)
    auth_NTLM = HTTPNtlmAuthHandler(passman)

    # disable proxies (just for testing)
    proxy_handler = urllib2.ProxyHandler({})

    opener = urllib2.build_opener(
        proxy_handler, auth_NTLM
    )  # , auth_digest, auth_basic)

    urllib2.install_opener(opener)

    response = urllib2.urlopen(url)
    print(response.read())
