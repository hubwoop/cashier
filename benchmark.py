import sqlite3
import itertools
import timeit

def setup_db():
    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE items_to_transactions (item integer, "transaction" integer)')
    return conn

receipt = {str(i): {'amount': 10} for i in range(100)} # 1000 rows

def original_map(db, receipt, transaction_id):
    for item_id, value in receipt.items():
        for _ in itertools.repeat(None, value['amount']):
            db.execute('insert into items_to_transactions (item, "transaction") values (?, ?)',
                       [int(item_id), transaction_id])
    db.commit()

def optimized_map(db, receipt, transaction_id):
    params = [
        (int(item_id), transaction_id)
        for item_id, value in receipt.items()
        for _ in itertools.repeat(None, value['amount'])
    ]
    db.executemany('insert into items_to_transactions (item, "transaction") values (?, ?)', params)
    db.commit()

db = setup_db()

print("Original time:", timeit.timeit(lambda: original_map(db, receipt, 1), number=100))
print("Optimized time:", timeit.timeit(lambda: optimized_map(db, receipt, 1), number=100))
