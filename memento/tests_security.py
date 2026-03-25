import unittest
from unittest.mock import MagicMock
from flask import Flask, session, request
from memento.auth import is_safe_url, auth_bp

class TestAuthSecurity(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'test'
        self.app.register_blueprint(auth_bp, url_prefix='/auth')
        self.client = self.app.test_client()

    def test_is_safe_url(self):
        with self.app.test_request_context(base_url='http://localhost:5002'):
            # Safe internal URLs
            self.assertTrue(is_safe_url('/'))
            self.assertTrue(is_safe_url('/dashboard'))
            self.assertTrue(is_safe_url('http://localhost:5002/dashboard'))

            # Unsafe external URLs
            self.assertFalse(is_safe_url('http://google.com'))
            self.assertFalse(is_safe_url('https://google.com'))
            self.assertFalse(is_safe_url('//google.com'))
            self.assertFalse(is_safe_url('javascript:alert(1)'))

    def test_login_redirect_validation(self):
        # Mock oauth.auth0.authorize_redirect to avoid AttributeError
        import memento.auth
        memento.auth.oauth = MagicMock()

        with self.app.test_request_context(base_url='http://localhost:5002'):
            # Test safe redirect
            with self.client as c:
                c.get('/auth/login?next=/safe')
                self.assertEqual(session.get('next'), '/safe')

            # Test unsafe redirect
            with self.client as c:
                c.get('/auth/login?next=http://malicious.com')
                self.assertEqual(session.get('next'), '/')

    def test_callback_redirect_validation(self):
        # Mock oauth.auth0.authorize_access_token and db.upsert_user
        import memento.auth
        memento.auth.oauth = MagicMock()
        memento.auth.oauth.auth0.authorize_access_token.return_value = {
            'userinfo': {'email': 'test@example.com', 'name': 'Test User', 'picture': '', 'sub': '123'}
        }
        import memento.db
        memento.db.upsert_user = MagicMock()

        with self.app.test_request_context(base_url='http://localhost:5002'):
            # Test safe redirect
            with self.client as c:
                with c.session_transaction() as sess:
                    sess['next'] = '/safe'
                c.get('/auth/callback')
                # session is popped, so we can't easily check it, but we can check the redirect location

            # Test unsafe redirect
            with self.client as c:
                with c.session_transaction() as sess:
                    sess['next'] = 'http://malicious.com'
                response = c.get('/auth/callback')
                self.assertEqual(response.location, '/')

if __name__ == '__main__':
    unittest.main()
