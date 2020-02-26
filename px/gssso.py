""" extract GS/GSSSO token

"""
import logging
import requests
from requests_kerberos import HTTPKerberosAuth

from cachetools.func import ttl_cache


class AuthFailed(Exception):
    pass


# cache for 10 mins
@ttl_cache(ttl=10 * 60)
def get_gssso():
    """ extract GSSSO based on kerbo, need kinit with tk file. """
    try:
        auth = HTTPKerberosAuth()
        req_session = requests.session()
        req_session.get(
            "https://authn.web.gs.com/desktopsso/Login", auth=auth, verify=True
        ).raise_for_status()
        return f"GSSSO={req_session.cookies['GSSSO']}"
    except Exception as e:
        logging.exception(e)
        raise AuthFailed()
