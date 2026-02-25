"""
Tests for item CRUD operations:
- show_items (GET /)
- add_item  (POST /add/item)
- get_item  (GET /get/item/<id>)
- delete_item (GET /delete/item/<id>/)
"""

import json

from cashier.db import get_db
from tests.conftest import login, add_item, add_item_with_image


class TestShowItems:
    """GET / — the item management page."""

    def test_empty_db_shows_no_items_message(self, auth_client):
        """Must be logged in to see the item list (and the empty message)."""
        resp = auth_client.get('/')
        assert b'No items here so far' in resp.data

    def test_shows_items_after_adding(self, auth_client):
        add_item(auth_client, title='Burger', price='5.00')
        resp = auth_client.get('/')
        assert b'Burger' in resp.data

    def test_shows_multiple_items(self, auth_client):
        add_item(auth_client, title='Burger', price='5.00')
        add_item(auth_client, title='Fries', price='3.00')
        resp = auth_client.get('/')
        assert b'Burger' in resp.data
        assert b'Fries' in resp.data

    def test_not_logged_in_shows_not_logged_in(self, client):
        resp = client.get('/')
        assert b'Not logged in' in resp.data


class TestAddItem:
    """POST /add/item — adding new items."""

    def test_add_item_success(self, auth_client):
        resp = add_item(auth_client, title='Pizza', price='8.50')
        assert b'New item was successfully added' in resp.data
        assert b'Pizza' in resp.data

    def test_add_item_persists_in_db(self, test_app, auth_client):
        add_item(auth_client, title='Salad', price='4.00', color='#00ff00')
        with test_app.app_context():
            db = get_db()
            cur = db.execute("SELECT title, price, color FROM items")
            row = cur.fetchone()
            assert row['title'] == 'Salad'
            assert row['price'] == 4.0
            assert row['color'] == '#00ff00'

    def test_add_item_price_with_comma(self, test_app, auth_client):
        """European-style comma decimal (e.g., '3,50') should be handled."""
        add_item(auth_client, title='Drink', price='3,50')
        with test_app.app_context():
            db = get_db()
            cur = db.execute("SELECT price FROM items WHERE title='Drink'")
            assert cur.fetchone()['price'] == 3.5

    def test_add_item_without_image(self, test_app, auth_client):
        add_item(auth_client, title='NoImage', price='1.00')
        with test_app.app_context():
            db = get_db()
            cur = db.execute("SELECT image_link FROM items WHERE title='NoImage'")
            assert cur.fetchone()['image_link'] is None

    def test_add_item_with_image(self, test_app, auth_client):
        add_item_with_image(auth_client, title='WithImage', price='2.00',
                            filename='burger.png')
        with test_app.app_context():
            db = get_db()
            cur = db.execute("SELECT image_link FROM items WHERE title='WithImage'")
            assert cur.fetchone()['image_link'] == 'burger.png'

    def test_add_item_rejects_disallowed_extension(self, test_app, auth_client):
        """Files with disallowed extensions should be ignored (no image stored)."""
        add_item_with_image(auth_client, title='BadExt', price='1.00',
                            filename='hack.exe')
        with test_app.app_context():
            db = get_db()
            cur = db.execute("SELECT image_link FROM items WHERE title='BadExt'")
            assert cur.fetchone()['image_link'] is None

    def test_add_item_redirects(self, auth_client):
        """After adding, should redirect to show_items."""
        resp = auth_client.post('/add/item', data={
            'title': 'X', 'price': '1', 'color': '#000'
        })
        assert resp.status_code == 302

    def test_add_item_invalid_price_flashes_error(self, auth_client):
        """Non-numeric price should flash an error, not crash with 500."""
        resp = add_item(auth_client, title='Bad', price='abc')
        assert resp.status_code == 200
        assert b'Invalid price' in resp.data

    def test_add_item_empty_price_flashes_error(self, auth_client):
        """Empty price should flash an error."""
        resp = add_item(auth_client, title='Empty', price='')
        assert resp.status_code == 200
        assert b'Invalid price' in resp.data

    def test_add_item_empty_title_flashes_error(self, auth_client):
        """Empty title should flash an error."""
        resp = auth_client.post('/add/item', data={
            'title': '', 'price': '1.00', 'color': '#000'
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Title is required' in resp.data


class TestGetItem:
    """GET /get/item/<id> — JSON API for fetching a single item."""

    def test_get_existing_item(self, test_app, auth_client):
        add_item(auth_client, title='Soup', price='3.00', color='#abcdef')
        resp = auth_client.get('/get/item/1')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['title'] == 'Soup'
        assert data['price'] == 3.0
        assert data['id'] == 1
        assert data['color'] == '#abcdef'

    def test_get_item_without_image(self, auth_client):
        add_item(auth_client, title='NoImg', price='1.00')
        resp = auth_client.get('/get/item/1')
        data = json.loads(resp.data)
        assert 'image_link' not in data

    def test_get_item_with_image(self, auth_client):
        add_item_with_image(auth_client, title='Img', price='2.00',
                            filename='test.jpg')
        resp = auth_client.get('/get/item/1')
        data = json.loads(resp.data)
        assert data['image_link'] == 'test.jpg'

    def test_get_nonexistent_item_returns_404(self, auth_client):
        resp = auth_client.get('/get/item/9999')
        assert resp.status_code == 404

    def test_get_item_returns_json(self, auth_client):
        add_item(auth_client, title='J', price='1')
        resp = auth_client.get('/get/item/1')
        # Should be valid JSON
        data = json.loads(resp.data)
        assert isinstance(data, dict)

    def test_get_item_content_type_is_json(self, auth_client):
        """Response must have Content-Type: application/json."""
        add_item(auth_client, title='CT', price='1')
        resp = auth_client.get('/get/item/1')
        assert resp.content_type == 'application/json'


class TestDeleteItem:
    """POST /delete/item/<id> — deleting items."""

    def test_delete_existing_item(self, test_app, auth_client):
        add_item(auth_client, title='ToDelete', price='1.00')
        resp = auth_client.post('/delete/item/1/', follow_redirects=True)
        assert resp.status_code == 200
        assert b'ToDelete' not in resp.data

    def test_delete_removes_from_db(self, test_app, auth_client):
        add_item(auth_client, title='Gone', price='1.00')
        auth_client.post('/delete/item/1/')
        with test_app.app_context():
            db = get_db()
            cur = db.execute("SELECT count(*) as cnt FROM items")
            assert cur.fetchone()['cnt'] == 0

    def test_delete_nonexistent_item_no_error(self, auth_client):
        """Deleting an item that doesn't exist should not crash."""
        resp = auth_client.post('/delete/item/9999/', follow_redirects=True)
        assert resp.status_code == 200

    def test_delete_redirects_to_index(self, auth_client):
        add_item(auth_client, title='X', price='1')
        resp = auth_client.post('/delete/item/1/')
        assert resp.status_code == 302

    def test_delete_one_of_multiple(self, test_app, auth_client):
        """Deleting one item should not affect others."""
        add_item(auth_client, title='Keep', price='1.00')
        add_item(auth_client, title='Remove', price='2.00')
        auth_client.post('/delete/item/2/')
        with test_app.app_context():
            db = get_db()
            cur = db.execute("SELECT title FROM items")
            rows = cur.fetchall()
            titles = [r['title'] for r in rows]
            assert 'Keep' in titles
            assert 'Remove' not in titles

    def test_delete_via_get_is_rejected(self, auth_client):
        """GET should not be allowed for delete — must use POST."""
        add_item(auth_client, title='NoGetDelete', price='1.00')
        resp = auth_client.get('/delete/item/1/')
        assert resp.status_code == 405
