import json
from io import BytesIO
from unittest import TestCase

try:
    from urllib2 import HTTPError, urlopen
    from urllib import urlencode
except ImportError:
    from urllib.request import urlopen
    from urllib.parse import urlencode, parse_qsl
    from urllib.error import HTTPError

import stepford


NUM_TEST_USERS = 3

CLIENT_ID = '290035784470436'
CLIENT_SECRET = '96b81e5dec11ef0081a8b02fa1054b66'
CLIENT_B_ID = '570048633057536'
CLIENT_B_SECRET = '97699b4b2deb8959131c861dc653f81e'


class TestStepford(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.access_token = stepford.app_token(CLIENT_ID, CLIENT_SECRET)
        cls.users = []
        for _ in range(NUM_TEST_USERS):
            cls.users.append(stepford.create(CLIENT_ID, cls.access_token))

    @classmethod
    def tearDownClass(cls):
        for user in cls.users:
            stepford.delete(user['id'], cls.access_token)

    def test_get(self):
        self.assertEqual(len(self.users), NUM_TEST_USERS)

        user_ids = set(map(lambda u: u['id'], self.users))
        fetched_user_ids = set(map(lambda u: u['id'], stepford.get(
            CLIENT_ID, self.access_token)))

        self.assertEqual(len(user_ids - fetched_user_ids), 0)

    def test_create_delete_success(self):
        user = stepford.create(CLIENT_ID, self.access_token)

        self.assertTrue(user['id'] in map(lambda u: u['id'], stepford.get(
            CLIENT_ID, self.access_token)))

        self.assertTrue(stepford.delete(user['id'], self.access_token))

        self.assertTrue(user['id'] not in map(lambda u: u['id'], stepford.get(
            CLIENT_ID, self.access_token)))

        try:
            stepford.delete(user['id'], self.access_token)
        except stepford.FacebookError as e:
            self.assertEqual(e.api_code, 
                stepford.API_EC_UNABLE_TO_ACCESS_APPLICATION)

    def test_connect_success(self):
        stepford.connect(*self.users)

        for user in self.users:
            # given user should be friends with everyone
            resp = urlopen('{}/me/friends?{}'.format(stepford._URIROOT,
                urlencode({'access_token': user['access_token']})))

            data = json.loads(resp.read().decode())

            lusers = set(map(lambda u: u['id'], self.users)) - set(
                [user['id']])
            rusers = set(map(lambda u: u['id'], stepford.get(CLIENT_ID,
                self.access_token)))

            self.assertEqual(len(lusers - rusers), 0)

        # TODO: reset connections if any other tests end up depending on clean
        # user state.

    def test_connect_single_user_error(self):
        self.assertRaises(ValueError, stepford.connect, (self.users[0],))

    def test_update_success(self):
        def _getname(token):
            resp = urlopen('{}/me?{}'.format(stepford._URIROOT, urlencode({
                'access_token': user['access_token']})))
            return json.loads(resp.read().decode())['name']

        user = self.users[0]
        stepford.update(user['id'], self.access_token, name='foo',
            pwd='flyingcircus')

        # because of the password change, we have to get the full list of app
        # test users (ew) in order to get the updated access_token or the user
        # we're currently working with.
        user['access_token'] = list(filter(lambda u: u['id'] == user['id'], 
            stepford.get(CLIENT_ID, self.access_token)))[0]['access_token']

        self.assertEqual(_getname(user['access_token']), 'foo')

    def test_update_error(self):
        try:
            stepford.update('123', self.access_token, name='WRONG')
        except stepford.FacebookError as e:
            self.assertEqual(e.api_code, 
                stepford.API_EC_UNABLE_TO_ACCESS_APPLICATION)

    def test_install_success(self):
        b_token = stepford.app_token(CLIENT_B_ID, CLIENT_B_SECRET)
        user = self.users[0]

        self.assertTrue(stepford.install(
            user['id'], b_token, CLIENT_ID, self.access_token,
            scope='read_stream'))

        resp = urlopen('{}/{}/ownerapps?{}'.format(stepford._URIROOT,
            user['id'], urlencode({
                'access_token': b_token, 
            })))
        self.assertTrue('stepford_b' in map(lambda app: app['name'],
            json.loads(resp.read().decode())['data']))

        try:
            # can't delete user account while other apps are still installed
            stepford.delete(user['id'], self.access_token)
        except stepford.FacebookError as e:
            self.assertEqual(e.api_code, 
                stepford.API_EC_TEST_ACCOUNTS_CANT_DELETE)

        self.assertTrue(stepford.uninstall(user['id'], CLIENT_B_ID, b_token))

    def test_something_bad_happened(self):
        urlopen_ = stepford.urlopen
        def _raise(url, *args, **kwargs):
            raise HTTPError(url, 500, 'err..', {},
                BytesIO('something bad happened'))

        stepford.urlopen = _raise
        try:
            token = stepford.app_token(CLIENT_ID, CLIENT_SECRET)
        except stepford.FacebookError as e:
            stepford.urlopen = urlopen_

            self.assertEqual(e.api_code, None)
            self.assertEqual(e.type, None)
            self.assertEqual(e.msg, 'Unhandled error')
