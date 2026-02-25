"""
Tests for helper / utility functions and miscellaneous behavior:
- format_price()
- file_allowed()
- customer_number management
- work_view route
- NewItem NamedTuple
"""

import cashier.printing as printing_mod
from cashier.helpers import format_price, file_allowed, NewItem
from tests.conftest import add_item


class TestFormatPrice:
    """Unit tests for price string normalization."""

    def test_dot_decimal(self):
        assert format_price('3.50') == 3.5

    def test_comma_decimal(self):
        assert format_price('3,50') == 3.5

    def test_integer_string(self):
        assert format_price('10') == 10.0

    def test_zero(self):
        assert format_price('0') == 0.0

    def test_large_number(self):
        assert format_price('999,99') == 999.99

    def test_invalid_price_raises(self):
        import pytest
        with pytest.raises(ValueError):
            format_price('abc')

    def test_empty_string_raises(self):
        import pytest
        with pytest.raises(ValueError):
            format_price('')


class TestFileAllowed:
    """Unit tests for file extension validation."""

    def test_png_allowed(self, test_app):
        assert file_allowed('photo.png') is True

    def test_jpg_allowed(self, test_app):
        assert file_allowed('photo.jpg') is True

    def test_jpeg_allowed(self, test_app):
        assert file_allowed('photo.jpeg') is True

    def test_gif_allowed(self, test_app):
        assert file_allowed('anim.gif') is True

    def test_svg_allowed(self, test_app):
        assert file_allowed('icon.svg') is True

    def test_bmp_allowed(self, test_app):
        assert file_allowed('pic.bmp') is True

    def test_ico_allowed(self, test_app):
        assert file_allowed('favicon.ico') is True

    def test_exe_not_allowed(self, test_app):
        assert file_allowed('virus.exe') is False

    def test_py_not_allowed(self, test_app):
        assert file_allowed('script.py') is False

    def test_no_extension_not_allowed(self, test_app):
        assert file_allowed('noextension') is False

    def test_case_insensitive(self, test_app):
        assert file_allowed('PHOTO.PNG') is True
        assert file_allowed('Photo.JpG') is True

    def test_double_extension(self, test_app):
        """Only the last extension is checked."""
        assert file_allowed('file.exe.png') is True
        assert file_allowed('file.png.exe') is False


class TestCustomerNumber:
    """Tests for global customer number management."""

    def test_initial_customer_number_type(self):
        assert isinstance(printing_mod.customer_number, int)

    def test_get_customer_number(self):
        original = printing_mod.customer_number
        try:
            printing_mod.customer_number = 42
            assert printing_mod.get_customer_number() == 42
        finally:
            printing_mod.customer_number = original

    def test_increase_customer_number(self):
        original = printing_mod.customer_number
        try:
            printing_mod.customer_number = 0
            printing_mod.increase_customer_number_by(1)
            assert printing_mod.customer_number == 1
            printing_mod.increase_customer_number_by(5)
            assert printing_mod.customer_number == 6
        finally:
            printing_mod.customer_number = original


class TestNewItem:
    """Tests for the NewItem NamedTuple."""

    def test_creation(self):
        item = NewItem(title='Burger', price=5.0, image_link=None, color='#ff0000')
        assert item.title == 'Burger'
        assert item.price == 5.0
        assert item.image_link is None
        assert item.color == '#ff0000'

    def test_is_tuple(self):
        item = NewItem(title='X', price=1.0, image_link=None, color='#000')
        assert isinstance(item, tuple)
        assert len(item) == 4

    def test_unpacking_order(self):
        """The order must match the DB insert column order."""
        item = NewItem(title='A', price=2.0, image_link='img.png', color='#fff')
        title, price, image_link, color = item
        assert title == 'A'
        assert price == 2.0
        assert image_link == 'img.png'
        assert color == '#fff'


class TestWorkView:
    """GET /work — the cashier work view."""

    def test_work_view_renders(self, client):
        resp = client.get('/work')
        assert resp.status_code == 200

    def test_work_view_shows_items(self, auth_client):
        add_item(auth_client, title='Hotdog', price='4.00')
        resp = auth_client.get('/work')
        assert b'Hotdog' in resp.data

    def test_work_view_shows_customer_number(self, auth_client):
        resp = auth_client.get('/work')
        assert b'Customer' in resp.data

    def test_work_view_increments_customer_number(self, client):
        """Each visit to /work should increment the customer number."""
        original = printing_mod.customer_number
        try:
            printing_mod.customer_number = 0
            client.get('/work')
            assert printing_mod.customer_number == 1
            client.get('/work')
            assert printing_mod.customer_number == 2
        finally:
            printing_mod.customer_number = original

    def test_work_view_not_logged_in(self, client):
        """Work view without login should show 'Not logged in'."""
        resp = client.get('/work')
        assert b'Not logged in' in resp.data


class TestEdgeCases:
    """Edge cases and regression tests."""

    def test_add_item_special_characters_in_title(self, test_app, auth_client):
        """Titles with special characters should be stored correctly."""
        add_item(auth_client, title='Börek & Çay', price='2.50')
        with test_app.app_context():
            from cashier.db import get_db
            db = get_db()
            cur = db.execute("SELECT title FROM items")
            assert cur.fetchone()['title'] == 'Börek & Çay'

    def test_add_item_large_price(self, test_app, auth_client):
        add_item(auth_client, title='Expensive', price='99999.99')
        with test_app.app_context():
            from cashier.db import get_db
            db = get_db()
            cur = db.execute("SELECT price FROM items WHERE title='Expensive'")
            assert cur.fetchone()['price'] == 99999.99

    def test_add_item_zero_price(self, test_app, auth_client):
        add_item(auth_client, title='Free', price='0')
        with test_app.app_context():
            from cashier.db import get_db
            db = get_db()
            cur = db.execute("SELECT price FROM items WHERE title='Free'")
            assert cur.fetchone()['price'] == 0.0
