"""
Shared pytest fixtures for the Cashier application test suite.

Provides:
- A test-configured Flask application (in-memory SQLite, testing mode)
- An initialized database
- A test client
- Authentication helpers
"""

import json
import tempfile
import pytest

from cashier.cashier import create_app
from cashier.db import init_db, get_db


@pytest.fixture
def test_app():
    """Create and configure a test application instance.

    Uses an in-memory SQLite DB so each test gets a clean,
    isolated database with zero filesystem overhead.
    """
    app = create_app({
        'TESTING': True,
        'DATABASE': 'file::memory:?cache=shared',
        'SECRET_KEY': 'test-secret-key',
        'USERNAME': 'admin',
        'PASSWORD': 'default',
        'PATH_TO_ITEM_IMAGES': tempfile.mkdtemp(),
        'WTF_CSRF_ENABLED': False,
    })

    with app.app_context():
        init_db()
        yield app


@pytest.fixture
def client(test_app):
    """A Flask test client for sending requests."""
    return test_app.test_client()


@pytest.fixture
def db(test_app):
    """Direct database connection within the app context."""
    with test_app.app_context():
        database = get_db()
        yield database


@pytest.fixture
def auth_client(client):
    """A test client that is already logged in."""
    client.post('/login', data={
        'username': 'admin',
        'password': 'default',
    }, follow_redirects=True)
    return client


# ── Helper functions for tests ──────────────────────────────────────

def login(client, username='admin', password='default'):
    """Log in via the login form."""
    return client.post('/login', data=dict(
        username=username,
        password=password,
    ), follow_redirects=True)


def logout(client):
    """Log out via the logout route."""
    return client.get('/logout', follow_redirects=True)


def add_item(client, title='Test Item', price='1.50', color='#ff0000'):
    """Add an item via the add_item form (requires logged-in client)."""
    return client.post('/add/item', data=dict(
        title=title,
        price=price,
        color=color,
    ), follow_redirects=True)


def add_item_with_image(client, title='Image Item', price='2.00',
                        color='#00ff00', image_data=b'fake-image-data',
                        filename='test.png'):
    """Add an item with an image upload."""
    from io import BytesIO
    data = {
        'title': title,
        'price': price,
        'color': color,
        'file': (BytesIO(image_data), filename),
    }
    return client.post('/add/item', data=data,
                       content_type='multipart/form-data',
                       follow_redirects=True)


def post_transaction(client, receipt_dict):
    """Post a transaction JSON payload."""
    return client.post('/add/transaction',
                       data=json.dumps(receipt_dict),
                       content_type='application/json')
