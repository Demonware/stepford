import json

from urllib2 import HTTPError, urlopen
from urllib import urlencode
from unittest import TestCase

import stepford

CLIENT_ID = '290035784470436'
CLIENT_SECRET = '96b81e5dec11ef0081a8b02fa1054b66'
CLIENT_B_ID = '570048633057536'
CLIENT_B_SECRET = '97699b4b2deb8959131c861dc653f81e'

class TestStepford(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.access_token = stepford.app_token(CLIENT_ID, CLIENT_SECRET)
        assert len(cls.access_token) > 0

    def test_create_get_delete(self):
        user = stepford.create(CLIENT_ID, self.access_token)
        self.assertIsNotNone(user['id'])

        users = stepford.get(CLIENT_ID, self.access_token)
        self.assertTrue(user['id'] in map(lambda u: u['id'], users))

        self.assertTrue(stepford.delete(user['id'], CLIENT_ID, 
            self.access_token))

        try:
            resp = stepford.delete(user['id'], CLIENT_ID, self.access_token)
        except HTTPError as e:
            self.assertEquals(e.code, 403)

    def test_connect(self):
        a = stepford.create(CLIENT_ID, self.access_token)
        b = stepford.create(CLIENT_ID, self.access_token)

        stepford.connect(a, b)

        resp = urlopen('{}/me/friends?{}'.format(stepford._URIROOT, urlencode({
            'access_token': a['access_token'],
        })))

        data = json.loads(resp.read())
        self.assertTrue(b['id'] in map(lambda u: u['id'], data['data']))

        stepford.delete(a['id'], CLIENT_ID, self.access_token)
        stepford.delete(b['id'], CLIENT_ID, self.access_token)

    def test_update(self):
        name = 'foo'
        user = stepford.create(CLIENT_ID, self.access_token)
        stepford.update(user['id'], self.access_token, name=name)

        resp = urlopen('{}/me?{}'.format(stepford._URIROOT, urlencode({
            'access_token': user['access_token'],
        })))
        self.assertEqual(json.loads(resp.read())['name'], name)

        stepford.delete(user['id'], CLIENT_ID, self.access_token)

    def test_install(self):
        b_token = stepford.app_token(CLIENT_B_ID, CLIENT_B_SECRET)
        user = stepford.create(CLIENT_ID, self.access_token)

        self.assertTrue(stepford.install(
            user['id'], b_token, CLIENT_ID, self.access_token))

        resp = urlopen('{}/{}/ownerapps?{}'.format(stepford._URIROOT,
            user['id'], urlencode({
                'access_token': b_token, 
            })))
        self.assertTrue('stepford_b' in map(lambda app: app['name'],
            json.loads(resp.read())['data']))

        try:
            # can't delete user account while other apps are still installed
            stepford.delete(user['id'], CLIENT_ID, self.access_token)
        except stepford.FacebookError as e:
            self.assertEqual(e.code, stepford.API_EC_TEST_ACCOUNTS_CANT_DELETE)

        self.assertTrue(stepford.uninstall(user['id'], CLIENT_B_ID, b_token))

        self.assertTrue(stepford.delete(user['id'], CLIENT_ID,
            self.access_token))
