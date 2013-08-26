from urllib2 import urlopen, HTTPError
from urllib import urlencode
from urlparse import parse_qsl
try:
    import simplejson as json
except ImportError:
    import json

_URIROOT = 'https://graph.facebook.com'

def get_app_token(client_id, client_secret):
    resp = urlopen('{}/oauth/access_token?{}'.format(_URIROOT, urlencode({
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    })))

    return dict(parse_qsl(resp.read()))['access_token']


def get_users(client_id, access_token):
    resp = urlopen('{}/{}/accounts/test-users?{}'.format(_URIROOT, 
        client_id, urlencode({'access_token': access_token})))
    
    return json.loads(resp.read())['data']


def create_user(client_id, access_token, installed=True, name=None,
                locale='en_US', permissions='read_stream'):
    resp = urlopen('{}/{}/accounts/test-users?{}'.format(
        _URIROOT,
        client_id,
        urlencode({
            'installed': installed,
            'locale': locale,
            'permissions': permissions,
            'method': post,
            'access_token': access_token,
        })))

    data = json.loads(resp.read())
    # TODO: check for 'error' in data and if the code is 2900 (too many test
    # users) 

    return json.loads(resp.read())
