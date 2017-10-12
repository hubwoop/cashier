import json
import os
import platform
import sqlite3
import subprocess
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from werkzeug.utils import secure_filename
from collections import namedtuple

app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file, cashier.py
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'bmp', 'ico'}
# Load default config
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'cashier.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default',
    PATH_TO_ITEM_IMAGES=os.path.join(app.root_path, 'static', 'images'),
    ALLOWED_EXTENSIONS=ALLOWED_EXTENSIONS
))
# And override config from an environment variable...
# Simply define the environment variable CASHIER_SETTINGS that points to a config file to be loaded.
app.config.from_envvar('CASHIER_SETTINGS', silent=True)


@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.route('/')
def show_items():
    db = get_db()
    cur = db.execute('select id, title, price, image_link, color from items order by id desc')
    items = cur.fetchall()
    return render_template('manage_items.html', items=items)


@app.route('/add/item', methods=['POST'])
def add_item():
    if not session.get('logged_in'):
        abort(401)
    price = float(request.form['price'])
    color = request.form['color']
    filename = None
    # check if the post request has the file part
    if 'file' in request.files:
        file = request.files['file']
        # check if the file part contains a value and is allowed
        if file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            try:
                file.save(os.path.join(app.config['PATH_TO_ITEM_IMAGES'], filename))
            except FileNotFoundError:
                os.mkdir(os.path.join(app.root_path, 'static', 'images'))
                file.save(os.path.join(app.config['PATH_TO_ITEM_IMAGES'], filename))
            color = None
    db = get_db()
    db.execute('insert into items (title, price, image_link, color) values (?, ?, ?, ?)',
               [request.form['title'], price, filename, color])
    db.commit()
    flash('New item was successfully added.')
    return redirect(url_for('show_items'))


@app.route('/get/item/<identifier>')
def get_item(identifier):
    try:
        int(identifier)
    except ValueError:
        abort(400)
    db = get_db()
    cur = db.execute('select id, title, price, image_link, color from items where id = (?)', [identifier])
    item = cur.fetchone()
    if not item:
        abort(400)
    item_for_json = {'id': item[0], 'title': item[1], 'price': item[2]}
    if item[3]:
        item_for_json.update({'image_link': item[3]})
    if item[4]:
        item_for_json.update({'color': item[4]})
    return json.dumps(item_for_json)


@app.route('/delete/item/<identifier>/')
def delete_item(identifier):
    if not session.get('logged_in'):
        abort(401)
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
    return render_template('work_view.html', items=items)


def print_receipt(data):
    if platform.system() == 'Windows':
        os.startfile("C:/Users/TestFile.txt", "print")
    elif platform.system() == 'Linux':
        lpr = subprocess.Popen("/usr/bin/lpr", stdin=subprocess.PIPE)
        lpr.stdin.write(data)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def dict_from_row(row):
    return dict(zip(row.keys(), row))


if __name__ == '__main__':
    app.run()
