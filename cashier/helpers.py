"""Utility functions, types, and auth helpers for the Cashier application."""

import os
from functools import wraps
from typing import NamedTuple, Optional

from flask import request, session, redirect, url_for, current_app
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'bmp', 'ico'}


class NewItem(NamedTuple):
    title: str
    price: float
    image_link: str
    color: str


# ── Auth ────────────────────────────────────────────────────────────

def login_required(fun):
    """Decorator that redirects unauthenticated users to the login page."""
    @wraps(fun)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login', next=request.url))
        return fun(*args, **kwargs)
    return decorated_function


# ── Price / file helpers ────────────────────────────────────────────

def format_price(price: str) -> float:
    """Normalize a price string (supporting comma decimals) to a float."""
    price = price.replace(',', '.')
    return float(price)


def file_allowed(filename) -> bool:
    """Check whether the filename has an allowed image extension."""
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS'])


def optionally_store_image() -> Optional[str]:
    """If a valid image was uploaded in the request, save it and return its filename."""
    filename = None
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '' and file_allowed(file.filename):
            filename = save_file_to_disk(file)
    return filename


def save_file_to_disk(file) -> str:
    """Save an uploaded file to the configured image directory."""
    filename = secure_filename(file.filename)
    try:
        file.save(os.path.join(current_app.config['PATH_TO_ITEM_IMAGES'], filename))
    except FileNotFoundError:
        os.mkdir(os.path.join(current_app.root_path, 'static', 'images'))
        file.save(os.path.join(current_app.config['PATH_TO_ITEM_IMAGES'], filename))
    return filename
