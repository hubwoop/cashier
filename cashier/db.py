"""Database access layer for the Cashier application."""

import itertools
import sqlite3
from datetime import datetime

from flask import g, current_app


def connect_db():
    """Open a new database connection, respecting URI-style paths."""
    db_path = current_app.config['DATABASE']
    if db_path.startswith('file:'):
        rv = sqlite3.connect(db_path, uri=True)
    else:
        rv = sqlite3.connect(db_path)
    rv.row_factory = sqlite3.Row
    rv.execute('pragma foreign_keys = on;')
    rv.commit()
    return rv


def get_db():
    """Return the request-scoped database connection, creating one if needed."""
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


def init_db():
    """Initialize the database from schema.sql."""
    db = get_db()
    with current_app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


def add_item_to_db(item):
    """Insert a new item into the database."""
    db = get_db()
    db.execute('insert into items (title, price, image_link, color) values (?, ?, ?, ?)', item)
    db.commit()


def fetch_item_from_db(identifier):
    """Fetch a single item by its ID."""
    db = get_db()
    cur = db.execute('select id, title, price, image_link, color from items where id = (?)',
                     [identifier])
    return cur.fetchone()


def store_transaction(receipt_sum: float) -> int:
    """Insert a transaction record and return its ID."""
    db = get_db()
    cursor = db.execute('insert into transactions (date, sum) values (?, ?)',
                        [str(datetime.now()), receipt_sum])
    transaction_id = int(cursor.lastrowid)
    db.commit()
    return transaction_id


def map_items_to_transaction(receipt: dict, transaction_id: int) -> None:
    """Create item-to-transaction mappings for each item in the receipt."""
    db = get_db()
    for item_id, value in receipt.items():
        for _ in itertools.repeat(None, value['amount']):
            db.execute('insert into items_to_transactions (item, "transaction") values (?, ?)',
                       [int(item_id), transaction_id])
    db.commit()
