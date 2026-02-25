"""Cashier application — routes and factory."""

import os

from flask import (Flask, request, session, g, redirect, url_for, abort,
                   render_template, flash, jsonify, current_app)

from cashier.db import (
    get_db, init_db, add_item_to_db, fetch_item_from_db,
    store_transaction, map_items_to_transaction,
)
from cashier.helpers import (
    ALLOWED_EXTENSIONS, NewItem, login_required,
    format_price, optionally_store_image,
)
from cashier.printing import (
    get_customer_number, increase_customer_number_by,
    process_receipt, prepare_receipt,
    build_kitchen_receipt, build_customer_receipt,
    print_receipt,
)


def create_app(config_from_params=None):
    """Application factory — creates and configures the Flask app."""
    app = Flask(__name__)

    # Default config
    app.config.update(
        DATABASE=os.path.join(app.root_path, 'cashier.db'),
        SECRET_KEY='development key',
        USERNAME='admin',
        PASSWORD='default',
        PATH_TO_ITEM_IMAGES=os.path.join(app.root_path, 'static', 'images'),
        ALLOWED_EXTENSIONS=ALLOWED_EXTENSIONS,
        PRINT_FILE=os.path.join(os.path.expanduser('~'), 'cashier_printfile.txt'),
    )

    if config_from_params is None:
        # Load config from environment variable if it exists
        app.config.from_envvar('CASHIER_SETTINGS', silent=True)
    else:
        app.config.update(config_from_params)

    # ── Routes ──────────────────────────────────────────────────────

    @app.route('/')
    def show_items():
        db = get_db()
        cur = db.execute('select id, title, price, image_link, color from items order by id desc')
        items = cur.fetchall()
        return render_template('manage_items.html', items=items)

    @app.route('/add/item', methods=['POST'])
    @login_required
    def add_item():
        title = request.form.get('title', '').strip()
        if not title:
            flash('Title is required.')
            return redirect(url_for('show_items'))
        try:
            price = format_price(request.form['price'])
        except (ValueError, KeyError):
            flash('Invalid price. Please enter a number.')
            return redirect(url_for('show_items'))
        new_item = NewItem(
            title=title,
            price=price,
            image_link=optionally_store_image(),
            color=request.form['color'],
        )
        add_item_to_db(new_item)
        flash('New item was successfully added.')
        return redirect(url_for('show_items'))

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
        return jsonify(item)

    @app.route('/delete/item/<int:identifier>/', methods=['POST'])
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
            if request.form['username'] != current_app.config['USERNAME']:
                error = 'Invalid username'
            elif request.form['password'] != current_app.config['PASSWORD']:
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
        """Store a completed sale transaction."""
        receipt, receipt_sum = process_receipt(request.get_json(force=True))
        transaction_id = store_transaction(receipt_sum)
        map_items_to_transaction(receipt, transaction_id)
        return jsonify(success=True)

    @app.route('/print/kitchen', methods=['POST'])
    @login_required
    def print_kitchen_receipt():
        receipt = request.get_json(force=True)  # type: dict
        items = {k: v for k, v in receipt.items() if k != 'sum'}
        text = build_kitchen_receipt(items)
        print_receipt(text + "\n\n\n\n\n")
        return jsonify(success=True)

    @app.route('/print/customer', methods=['POST'])
    @login_required
    def print_customer_receipt():
        receipt, receipt_sum = prepare_receipt()
        text = build_customer_receipt(receipt, receipt_sum)
        print_receipt(text)
        return jsonify(success=True)

    # ── CLI commands ────────────────────────────────────────────────

    @app.cli.command('initdb')
    def init_db_command():
        init_db()
        print('Initialized the database.')

    # ── Teardown ────────────────────────────────────────────────────

    @app.teardown_appcontext
    def close_db(error):
        if hasattr(g, 'sqlite_db'):
            g.sqlite_db.close()

    return app


# ── Backward compatibility ──────────────────────────────────────────
# Create a default app instance so `flask run` and `from cashier import app` still work.
app = create_app()

if __name__ == '__main__':
    app.run()
