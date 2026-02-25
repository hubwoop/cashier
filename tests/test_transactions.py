"""
Tests for the transaction workflow:
- POST /add/transaction
- process_receipt()
- store_transaction()
- map_items_to_transaction()
"""

import json

from cashier.db import get_db
from tests.conftest import add_item, post_transaction


class TestAddTransaction:
    """POST /add/transaction — storing a completed sale."""

    def _seed_items(self, auth_client):
        """Add two items to work with."""
        add_item(auth_client, title='Burger', price='5.00')
        add_item(auth_client, title='Fries', price='3.00')

    def test_transaction_success(self, auth_client):
        self._seed_items(auth_client)
        receipt = {
            'sum': 8.0,
            '1': {'amount': 1, 'title': 'Burger', 'price': 5.0},
            '2': {'amount': 1, 'title': 'Fries', 'price': 3.0},
        }
        resp = post_transaction(auth_client, receipt)
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['success'] is True

    def test_transaction_creates_db_record(self, test_app, auth_client):
        self._seed_items(auth_client)
        receipt = {
            'sum': 5.0,
            '1': {'amount': 1, 'title': 'Burger', 'price': 5.0},
        }
        post_transaction(auth_client, receipt)
        with test_app.app_context():
            db = get_db()
            cur = db.execute("SELECT sum FROM transactions")
            row = cur.fetchone()
            assert row['sum'] == 5.0

    def test_transaction_maps_items(self, test_app, auth_client):
        self._seed_items(auth_client)
        receipt = {
            'sum': 11.0,
            '1': {'amount': 2, 'title': 'Burger', 'price': 5.0},
            '2': {'amount': 1, 'title': 'Fries', 'price': 3.0},
        }
        post_transaction(auth_client, receipt)
        with test_app.app_context():
            db = get_db()
            cur = db.execute(
                'SELECT item, "transaction" FROM items_to_transactions'
            )
            rows = cur.fetchall()
            # 2x Burger + 1x Fries = 3 mapping rows
            assert len(rows) == 3
            item_ids = [r['item'] for r in rows]
            assert item_ids.count(1) == 2  # Burger x2
            assert item_ids.count(2) == 1  # Fries x1

    def test_transaction_stores_date(self, test_app, auth_client):
        self._seed_items(auth_client)
        receipt = {
            'sum': 5.0,
            '1': {'amount': 1, 'title': 'Burger', 'price': 5.0},
        }
        post_transaction(auth_client, receipt)
        with test_app.app_context():
            db = get_db()
            cur = db.execute("SELECT date FROM transactions")
            row = cur.fetchone()
            assert row['date'] is not None
            assert len(row['date']) > 0

    def test_multiple_transactions(self, test_app, auth_client):
        self._seed_items(auth_client)
        for i in range(3):
            receipt = {
                'sum': 5.0,
                '1': {'amount': 1, 'title': 'Burger', 'price': 5.0},
            }
            post_transaction(auth_client, receipt)
        with test_app.app_context():
            db = get_db()
            cur = db.execute("SELECT count(*) as cnt FROM transactions")
            assert cur.fetchone()['cnt'] == 3

    def test_transaction_with_zero_sum(self, auth_client):
        """Edge case: a transaction with sum 0."""
        resp = post_transaction(auth_client, {'sum': 0.0})
        assert resp.status_code == 200

    def test_transaction_response_content_type(self, auth_client):
        """Response must have Content-Type: application/json."""
        self._seed_items(auth_client)
        receipt = {
            'sum': 5.0,
            '1': {'amount': 1, 'title': 'Burger', 'price': 5.0},
        }
        resp = post_transaction(auth_client, receipt)
        assert resp.content_type == 'application/json'


class TestProcessReceipt:
    """Unit tests for process_receipt helper."""

    def test_extracts_sum(self):
        from cashier.printing import process_receipt
        receipt = {'sum': 10.5, '1': {'amount': 1, 'title': 'x', 'price': 10.5}}
        result, receipt_sum = process_receipt(receipt)
        assert receipt_sum == 10.5

    def test_removes_sum_key(self):
        from cashier.printing import process_receipt
        receipt = {'sum': 10.5, '1': {'amount': 1, 'title': 'x', 'price': 10.5}}
        result, _ = process_receipt(receipt)
        assert 'sum' not in result

    def test_preserves_items(self):
        from cashier.printing import process_receipt
        receipt = {
            'sum': 5.0,
            '1': {'amount': 1, 'title': 'Burger', 'price': 5.0},
            '2': {'amount': 2, 'title': 'Fries', 'price': 3.0},
        }
        result, _ = process_receipt(receipt)
        assert '1' in result
        assert '2' in result

    def test_does_not_mutate_original_dict(self):
        """process_receipt must NOT modify the caller's dict."""
        from cashier.printing import process_receipt
        original = {'sum': 10.0, '1': {'amount': 1, 'title': 'x', 'price': 10.0}}
        original_copy = original.copy()
        process_receipt(original)
        assert 'sum' in original, "Original dict was mutated — 'sum' key was deleted"
        assert original == original_copy
