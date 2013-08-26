from unittest import TestCase

import stepford

CLIENT_ID = '290035784470436'
CLIENT_SECRET = '0d28c04c4334be1c2910a77547cdea3d'

class TestStepford(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.access_token = stepford.get_app_token(CLIENT_ID, CLIENT_SECRET)
        assert len(cls.access_token) > 0

    def test_get_users(self):
        users = stepford.get_users(CLIENT_ID, self.access_token)
        self.assertEqual(len(users), 0)
