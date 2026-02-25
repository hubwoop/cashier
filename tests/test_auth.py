"""
Tests for authentication: login, logout, session management, and the
login_required decorator.
"""

from tests.conftest import login, logout


class TestLogin:
    """Login route and authentication behavior."""

    def test_login_page_renders(self, client):
        """GET /login should return the login form."""
        resp = client.get('/login')
        assert resp.status_code == 200
        assert b'Login' in resp.data
        assert b'Username' in resp.data

    def test_successful_login(self, client):
        resp = login(client, 'admin', 'default')
        assert resp.status_code == 200
        assert b'You were logged in' in resp.data

    def test_login_wrong_username(self, client):
        resp = login(client, 'wrong', 'default')
        assert b'Invalid username' in resp.data

    def test_login_wrong_password(self, client):
        resp = login(client, 'admin', 'wrong')
        assert b'Invalid password' in resp.data

    def test_login_wrong_both(self, client):
        resp = login(client, 'wrong', 'wrong')
        assert b'Invalid username' in resp.data

    def test_login_sets_session(self, client):
        """After login, the session should contain 'logged_in'."""
        login(client)
        with client.session_transaction() as sess:
            assert sess.get('logged_in') is True


class TestLogout:
    """Logout route behavior."""

    def test_logout_clears_session(self, client):
        login(client)
        logout(client)
        with client.session_transaction() as sess:
            assert sess.get('logged_in') is None

    def test_logout_flash_message(self, client):
        login(client)
        resp = logout(client)
        assert b'You were logged out' in resp.data

    def test_logout_redirects_to_index(self, client):
        login(client)
        resp = client.get('/logout')
        assert resp.status_code == 302


class TestLoginRequired:
    """Routes protected by @login_required should redirect when not logged in."""

    def test_add_item_requires_login(self, client):
        resp = client.post('/add/item', data={
            'title': 'x', 'price': '1', 'color': '#fff'
        })
        assert resp.status_code == 302
        assert '/login' in resp.headers.get('Location', '')

    def test_delete_item_requires_login(self, client):
        resp = client.post('/delete/item/1/')
        assert resp.status_code == 302
        assert '/login' in resp.headers.get('Location', '')

    def test_get_item_requires_login(self, client):
        resp = client.get('/get/item/1')
        assert resp.status_code == 302
        assert '/login' in resp.headers.get('Location', '')

    def test_add_transaction_requires_login(self, client):
        resp = client.post('/add/transaction',
                           data='{"sum": 0}',
                           content_type='application/json')
        assert resp.status_code == 302

    def test_print_kitchen_requires_login(self, client):
        resp = client.post('/print/kitchen',
                           data='{"sum": 0}',
                           content_type='application/json')
        assert resp.status_code == 302

    def test_print_customer_requires_login(self, client):
        resp = client.post('/print/customer',
                           data='{"sum": 0}',
                           content_type='application/json')
        assert resp.status_code == 302

    def test_show_items_is_public(self, client):
        """The index / manage_items page does NOT require login."""
        resp = client.get('/')
        assert resp.status_code == 200

    def test_work_view_is_public(self, client):
        """The work view does NOT currently require login."""
        resp = client.get('/work')
        assert resp.status_code == 200
