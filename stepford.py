""" Implementation of the Facebook test user API
"""

from functools import wraps
try:
    from urllib2 import urlopen, HTTPError
    from urllib import urlencode
    from urlparse import parse_qsl
except ImportError:
    from urllib.request import urlopen
    from urllib.parse import urlencode, parse_qsl
    from urllib.error import HTTPError
try:
    import simplejson as json
except ImportError:
    import json

_URIROOT = 'https://graph.facebook.com'

# as documented @ https://developers.facebook.com/docs/test_users/
API_EC_TEST_ACCOUNTS_CANT_DELETE = 2903
API_EC_TEST_ACCOUNTS_CANT_REMOVE_APP = 2902
API_EC_TEST_ACCOUNTS_INVALID_ID = 2901
API_EC_TEST_ACCOUNTS_TOO_MANY = 2900

# other errors encountered
API_EC_UNABLE_TO_ACCESS_APPLICATION = 200


class FacebookError(HTTPError): # pylint: disable=R0901
    """ Exposes Facebook-specific error attributes

    Methods wrapped with :meth:`stepford.translate_http_error` will raise a
    :class:`stepford.FacebookError` whenever an :py:class:`urllib2.HTTPError` is
    encountered. This helps expose more detailed information about the error
    than the simple HTTP error code and message.

    In the event that ``stepford`` encounters an unexpected API error (i.e. one
    that doesn't contain the usual error data payload),
    :attr:`~stepford.FacebookError.api_code` and
    :attr:`~stepford.FacebookError.type` will be set to ``None``.

    .. attribute:: api_code

       The Facebook client-facing error code

    .. attribute:: type

       The error category as defined by Facebook
    """
    def __init__(self, err):
        try:
            data = json.loads(err.fp.read().decode())['error']
        except (ValueError, KeyError):
            # something REALLY bad happened and Facebook didn't send along
            # their usual error payload
            data = {
                'message': 'Unhandled error',
                'code': None,
                'type': None,
            }

        HTTPError.__init__(self, err.url, err.code, data['message'],
            err.headers, err.fp)

        self.api_code = data['code']
        self.type = data['type']


def translate_http_error(func):
    """ HTTPError to FacebookError translation decorator

    Decorates functions, handles :py:class:`urllib2.HTTPError` exceptions and
    translates them into :class:`stepford.FacebookError`

    :param func: The function to decorate with translation handling
    """
    @wraps(func)
    def inner(*args, **kwargs): # pylint: disable=C0111
        try:
            return func(*args, **kwargs)
        except HTTPError as err:
            raise FacebookError(err)
    return inner


@translate_http_error
def app_token(client_id, client_secret):
    """ Gets the app token

    The app token is used in all ``stepford`` transactions. It is provided by
    Facebook and only changes when your app secret has been changed.

    :param client_id: Your app's client ID, as provided by Facebook
    :param client_secret: Your app's client secret, as provided by Facebook

    :return: A dict containing the app token
    """
    resp = urlopen('{}/oauth/access_token?{}'.format(_URIROOT, urlencode({
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    })))

    return dict(parse_qsl(resp.read().decode()))['access_token']


@translate_http_error
def get(client_id, access_token):
    """ Gets a list of available test users

    :param client_id: Your app's client ID, as provided by Facebook
    :param access_token: Your app's access_token, as retrieved by ``app_token``
                         (alternatively, this can be retrieved by Facebook's
                         testing toolset).
    
    :return: A list of ``dict`` elements containing user details
    """
    resp = urlopen('{}/{}/accounts/test-users?{}'.format(_URIROOT,
        client_id, urlencode({'access_token': access_token})))

    return json.loads(resp.read().decode())['data']


# pylint: disable=R0913
@translate_http_error
def create(client_id, access_token, installed=True, name=None,
    locale='en_US', permissions='read_stream'):
    """ Creates a test user

    :param client_id: Your app's client ID, as provided by Facebook
    :param access_token: Your app's access_token, as retrieved by ``app_token``
                         (alternatively, this can be retrieved by Facebook's
                         testing toolset).
    :param installed: Whether or not the user should be created with your app
                      installed.
    :param name: The name of the test user. If ``None``, this will be
                 auto-generated by Facebook.
    :param locale: The user's default locale.
    :param permissions: The scope approved by the test user. This should be a
                        comma-delimited list of resource types approved by this
                        user for your application.

    :return: A ``dict`` containing user details
    """
    resp = urlopen('{}/{}/accounts/test-users?{}'.format(
        _URIROOT,
        client_id,
        urlencode({
            'installed': installed,
            'locale': locale,
            'permissions': permissions,
            'method': 'post',
            'access_token': access_token,
            'name': name,
        })))

    return json.loads(resp.read().decode())


@translate_http_error
def delete(userid, access_token):
    """ Deletes a test user

    :param userid: The ID of the user to delete.
    :param client_id: Your app's client ID, as provided by Facebook
    :param access_token: Your app's access_token, as retrieved by ``app_token``
                         (alternatively, this can be retrieved by Facebook's
                         testing toolset).

    :return: ``True`` on success
    """
    resp = urlopen('{}/{}?{}'.format(_URIROOT, userid, urlencode({
        'method': 'delete',
        'access_token': access_token,
    })))

    return resp.read() == b'true'


@translate_http_error
def connect(*users):
    """ Creates friendships between test user accounts

    :param users: A list of users to create friendships for.
    """
    if len(users) <= 1:
        raise ValueError('len(users) must be > 1')

    def _connect(user_a, user_b): # pylint: disable=C0111
        return urlopen('{}/{}/friends/{}?{}'.format(_URIROOT,
            user_a['id'], user_b['id'], urlencode({
                'access_token': user_a['access_token'],
                'method': 'post'
            })))

    for idx, user_a in enumerate(users[:-1]):
        for user_b in users[idx + 1:]:
            _connect(user_a, user_b)
            _connect(user_b, user_a)


@translate_http_error
def update(userid, access_token, name=None, pwd=None):
    """ Updates the given user

    :param userid: The ID of the user to be updated
    :param access_token: The app access token
    :param name (optional): If specified, what name to assign to the user
    :param pwd (optional): If specified, what password to assign to the user

    :return: ``True`` on success
    """
    query = {
        'method': 'post',
        'access_token': access_token,
    }
    if name is not None:
        query['name'] = name

    if pwd is not None:
        query['password'] = pwd

    resp = urlopen('{}/{}?{}'.format(_URIROOT, userid, urlencode(query)))
    return resp.code == 200


@translate_http_error
def install(userid, install_to_token, clientid, access_token, scope=None):
    """ Installs an app for the given user

    :param userid: The user to install the app for
    :param install_to_token: The app token for the app being installed
    :param clientid: The client_id of the app that owns the test user
    :param access_token: The app token of the app that owns the test user
    :param scope: The scope to install the app for the test user with

    :return: ``True`` on success
    """
    query = {
        'installed': 'true',
        'uid': userid,
        'owner_access_token': access_token,
        'access_token': install_to_token,
        'method': 'post',
    }
    if scope is not None:
        query['scope'] = scope

    resp = urlopen('{}/{}/accounts/test-users?{}'.format(_URIROOT,
        clientid, urlencode(query)))
    return resp.code == 200


@translate_http_error
def uninstall(userid, clientid, access_token):
    """ Uninstalls an app for the given user

    :param userid: The user to uninstall the app for
    :param clientid: The client id of the app being removed
    :param access_token: The access token of the app being removed

    :return: ``True`` on success
    """
    resp = urlopen('{}/{}/accounts/test-users?{}'.format(_URIROOT,
        clientid, urlencode({
            'access_token': access_token,
            'method': 'delete',
            'uid': userid,
        })))
    return resp.code == 200
