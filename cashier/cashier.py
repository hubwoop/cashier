import json
import os
import platform
import sqlite3
import subprocess
import itertools
from datetime import datetime
from functools import wraps
from typing import NamedTuple, Optional

from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file, cashier.py
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'bmp', 'ico'}
PRINTER_PATH_LINUX = "/dev/usb/pl0"
ASCII_SEPARATOR = "-----------------------"
# Load default config
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'cashier.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default',
    PATH_TO_ITEM_IMAGES=os.path.join(app.root_path, 'static', 'images'),
    ALLOWED_EXTENSIONS=ALLOWED_EXTENSIONS,
    PRINT_FILE=os.path.join(os.path.expanduser('~'), 'cashier_printfile.txt')
))
# And override config from an environment variable...
# Simply define the environment variable CASHIER_SETTINGS that points to a config file to be loaded.
app.config.from_envvar('CASHIER_SETTINGS', silent=True)
customer_number = 0


class NewItem(NamedTuple):
    title: str
    price: float
    image_link: str
    color: str


def login_required(fun):
    @wraps(fun)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login', next=request.url))
        return fun(*args, **kwargs)

    return decorated_function


@app.route('/')
def show_items():
    db = get_db()
    cur = db.execute('select id, title, price, image_link, color from items order by id desc')
    items = cur.fetchall()
    return render_template('manage_items.html', items=items)


@app.route('/add/item', methods=['POST'])
@login_required
def add_item():
    new_item = build_new_item()
    add_item_to_db(new_item)
    flash('New item was successfully added.')
    return redirect(url_for('show_items'))


def build_new_item() -> NewItem:
    return NewItem(title=request.form['title'],
                   price=format_price(request.form['price']),
                   image_link=optionally_store_image(),
                   color=request.form['color'])


def format_price(price: str) -> float:
    price = price.replace(',', '.')
    return float(price)


def optionally_store_image() -> Optional[str]:
    filename = None
    # check if the post request has the file part
    if 'file' in request.files:
        file = request.files['file']
        # check if the file part contains a value and is allowed
        if file.filename != '' and file_allowed(file.filename):
            filename = save_file_to_disk(file)
    return filename


def file_allowed(filename) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def save_file_to_disk(file) -> str:
    filename = secure_filename(file.filename)
    try:
        file.save(os.path.join(app.config['PATH_TO_ITEM_IMAGES'], filename))
    except FileNotFoundError:
        os.mkdir(os.path.join(app.root_path, 'static', 'images'))
        file.save(os.path.join(app.config['PATH_TO_ITEM_IMAGES'], filename))
    return filename


def add_item_to_db(item):
    db = get_db()
    db.execute('insert into items (title, price, image_link, color) values (?, ?, ?, ?)', item)
    db.commit()


@app.route('/get/item/<int:identifier>')
@login_required
def get_item(identifier):
    item_row = fetch_item_from_db(identifier)
    if not item_row:
        abort(404)
    item = {'id': item_row[0], 'title': item_row[1], 'price': item_row[2]}
    if item_row[3]:
        item.update({'image_link': item_row[3]})
    if item_row[4]:
        item.update({'color': item_row[4]})
    return json.dumps(item)


def fetch_item_from_db(identifier):
    db = get_db()
    cur = db.execute('select id, title, price, image_link, color from items where id = (?)', [identifier])
    return cur.fetchone()


@app.route('/delete/item/<int:identifier>/')
@login_required
def delete_item(identifier):
    db = get_db()
    db.execute('delete from items where id = (?)', [identifier])
    db.commit()
    return redirect(url_for('show_items'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_items'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_items'))


@app.route('/work')
def work_view():
    db = get_db()
    cur = db.execute('select id, title, price, image_link, color from items order by id desc')
    items = cur.fetchall()
    increase_customer_number_by(1)
    return render_template('work_view.html', items=items, customer=get_customer_number())


@app.route('/add/transaction', methods=['POST'])
@login_required
def add_transaction():

    """
    This API method is called when a customer is served to store the transaction
    """

    receipt, receipt_sum = process_receipt(request.get_json(force=True))
    transaction_id = store_transaction(receipt_sum)
    map_items_to_transaction(receipt, transaction_id)
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


def process_receipt(receipt: dict):
    receipt_sum = float(receipt['sum'])
    del receipt['sum']
    return receipt, receipt_sum


def store_transaction(receipt_sum: float) -> int:
    db = get_db()
    cursor = db.execute('insert into transactions (date, sum) values (?, ?)',
                        [str(datetime.now()), receipt_sum])
    transaction_id = int(cursor.lastrowid)
    db.commit()
    return transaction_id


def map_items_to_transaction(receipt: dict, transaction_id: int) -> None:
    db = get_db()
    for item_id, value in receipt.items():
        for _ in itertools.repeat(None, value['amount']):
            db.execute('insert into items_to_transactions (item, "transaction") values (?, ?)',
                       [int(item_id), transaction_id])
    db.commit()


@app.route('/print/kitchen', methods=['POST'])
@login_required
def print_kitchen_receipt():
    receipt = request.get_json(force=True)  # type: dict
    del receipt['sum']
    text = build_kitchen_receipt(receipt)
    print_receipt(text + "\n\n\n\n\n")
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


def build_kitchen_receipt(receipt: dict) -> str:
    text = f"Bestellung #{get_customer_number() % 100}{ASCII_SEPARATOR}\n"
    text += build_item_listing(receipt)
    return text


@app.route('/print/customer', methods=['POST'])
@login_required
def print_customer_receipt():
    receipt, receipt_sum = prepare_receipt()
    text = build_customer_receipt(receipt, receipt_sum)
    print_receipt(text)
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


def prepare_receipt():
    receipt = request.get_json(force=True)  # type: dict
    receipt_sum = float(receipt['sum'])
    del receipt['sum']
    return receipt, receipt_sum


def build_customer_receipt(receipt: dict, receipt_sum: float) -> str:
    text = f"\n\nDeine Nummer: - {get_customer_number() % 100} - \n\n\n\n{ASCII_SEPARATOR}"
    text += build_item_listing(receipt)
    text += f"\n{ASCII_SEPARATOR}\nSumme: {receipt_sum} €"
    return text


def build_item_listing(receipt: dict) -> str:
    item_listing = ""
    for item_id, value in receipt.items():
        item_listing += f'\n {value["amount"]}x {value["title"]}'
    return item_listing


def print_receipt(text: str) -> None:
    print(text)
    if platform.system() == 'Windows':
        print_like_windows(text)
    elif platform.system() == 'Linux':
        print_like_linux(text)
    else:
        raise NotImplementedError("Printing on your platform is currently not supported.")


def print_like_windows(text):
    with open(app.config['PRINT_FILE']) as f:
        f.write(text)
    os.startfile(app.config['PRINT_FILE'], "print")


def print_like_linux(text):
    line_printer_process = subprocess.run([PRINTER_PATH_LINUX], stdin=subprocess.PIPE)
    line_printer_process.stdin.write(str.encode(text))


@app.cli.command('initdb')
def init_db_command():
    init_db()
    print('Initialized the database.')


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    rv.execute('pragma foreign_keys = on;')
    rv.commit()
    return rv


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


def get_customer_number() -> int:
    global customer_number
    return customer_number


def increase_customer_number_by(integer: int):
    global customer_number
    customer_number += integer


if __name__ == '__main__':
    app.run()
