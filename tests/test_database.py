"""
Tests for database initialization, schema integrity, and fixture sanity.
"""

from cashier.db import get_db


class TestApplicationFactory:
    """Verify that the create_app factory pattern works."""

    def test_create_app_returns_flask_app(self):
        from cashier.cashier import create_app
        app = create_app()
        assert app is not None
        assert app.name == 'cashier.cashier'

    def test_create_app_accepts_test_config(self):
        from cashier.cashier import create_app
        app = create_app({'TESTING': True, 'DATABASE': 'file::memory:?cache=shared'})
        assert app.config['TESTING'] is True

    def test_create_app_does_not_share_state(self):
        """Two create_app calls should produce independent apps."""
        from cashier.cashier import create_app
        app1 = create_app({'SECRET_KEY': 'key1'})
        app2 = create_app({'SECRET_KEY': 'key2'})
        assert app1.config['SECRET_KEY'] != app2.config['SECRET_KEY']


class TestDatabaseSetup:
    """Verify that the test DB is initialized correctly."""

    def test_db_tables_exist(self, test_app):
        """All three tables from schema.sql must be present."""
        with test_app.app_context():
            db = get_db()
            cur = db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = sorted(row['name'] for row in cur.fetchall())
            assert 'items' in tables
            assert 'transactions' in tables
            assert 'items_to_transactions' in tables

    def test_items_table_columns(self, test_app):
        """The items table must have the expected columns."""
        with test_app.app_context():
            db = get_db()
            cur = db.execute("PRAGMA table_info(items)")
            columns = {row['name'] for row in cur.fetchall()}
            assert columns == {'id', 'title', 'price', 'image_link', 'color'}

    def test_transactions_table_columns(self, test_app):
        with test_app.app_context():
            db = get_db()
            cur = db.execute("PRAGMA table_info(transactions)")
            columns = {row['name'] for row in cur.fetchall()}
            assert columns == {'id', 'date', 'sum'}

    def test_items_to_transactions_table_columns(self, test_app):
        with test_app.app_context():
            db = get_db()
            cur = db.execute("PRAGMA table_info(items_to_transactions)")
            columns = {row['name'] for row in cur.fetchall()}
            assert columns == {'item', 'transaction'}

    def test_empty_db_has_no_items(self, test_app):
        """A freshly initialized DB should have zero items."""
        with test_app.app_context():
            db = get_db()
            cur = db.execute("SELECT count(*) as cnt FROM items")
            assert cur.fetchone()['cnt'] == 0

    def test_empty_db_has_no_transactions(self, test_app):
        with test_app.app_context():
            db = get_db()
            cur = db.execute("SELECT count(*) as cnt FROM transactions")
            assert cur.fetchone()['cnt'] == 0

    def test_foreign_key_enforcement(self, test_app):
        """Foreign keys should be enforced (PRAGMA foreign_keys = ON)."""
        import sqlite3 as sqlite3_mod
        with test_app.app_context():
            db = get_db()
            # Insert a valid item first
            db.execute("INSERT INTO items (title, price) VALUES ('x', 1.0)")
            db.commit()
            # Try to insert an items_to_transactions referencing a non-existent transaction
            try:
                db.execute(
                    'INSERT INTO items_to_transactions (item, "transaction") VALUES (1, 9999)'
                )
                db.commit()
                # If we get here, FK enforcement may be off — this should fail
                assert False, "Foreign key constraint was not enforced"
            except sqlite3_mod.IntegrityError:
                pass  # Expected


class TestFixtures:
    """Verify that the test fixtures work correctly."""

    def test_client_fixture(self, client):
        """The test client must be usable."""
        resp = client.get('/')
        assert resp.status_code == 200

    def test_auth_client_is_logged_in(self, auth_client):
        """The auth_client fixture must be pre-authenticated."""
        resp = auth_client.get('/')
        assert b'log out' in resp.data

    def test_db_isolation(self, test_app):
        """Each test gets its own clean database."""
        with test_app.app_context():
            db = get_db()
            db.execute("INSERT INTO items (title, price) VALUES ('isolation', 1.0)")
            db.commit()
            cur = db.execute("SELECT count(*) as cnt FROM items")
            assert cur.fetchone()['cnt'] == 1
        # Next test should not see this item — isolation is per-fixture invocation

    def test_db_isolation_verifier(self, test_app):
        """Companion to above — the 'isolation' item must not exist here."""
        with test_app.app_context():
            db = get_db()
            cur = db.execute("SELECT count(*) as cnt FROM items")
            assert cur.fetchone()['cnt'] == 0
