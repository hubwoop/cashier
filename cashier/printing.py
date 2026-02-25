"""Receipt building, printing, and customer number management."""

import os
import platform
import subprocess

from flask import request, current_app

PRINTER_PATH_LINUX = "/dev/usb/pl0"
ASCII_SEPARATOR = "-----------------------"

customer_number = 0


# ── Customer number ─────────────────────────────────────────────────

def get_customer_number() -> int:
    global customer_number
    return customer_number


def increase_customer_number_by(integer: int):
    global customer_number
    customer_number += integer


# ── Receipt processing ──────────────────────────────────────────────

def process_receipt(receipt: dict):
    """Extract the sum and item entries from a receipt dict (non-mutating)."""
    receipt_sum = float(receipt['sum'])
    items = {k: v for k, v in receipt.items() if k != 'sum'}
    return items, receipt_sum


def prepare_receipt():
    """Parse the receipt from the current request JSON."""
    receipt = request.get_json(force=True)  # type: dict
    receipt_sum = float(receipt['sum'])
    items = {k: v for k, v in receipt.items() if k != 'sum'}
    return items, receipt_sum


# ── Receipt builders ────────────────────────────────────────────────

def build_kitchen_receipt(receipt: dict) -> str:
    text = f"Bestellung #{get_customer_number() % 100}{ASCII_SEPARATOR}\n"
    text += build_item_listing(receipt)
    return text


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


# ── Printer dispatch ────────────────────────────────────────────────

def print_receipt(text: str) -> None:
    print(text)
    if platform.system() == 'Windows':
        print_like_windows(text)
    elif platform.system() == 'Linux':
        print_like_linux(text)
    elif platform.system() == 'Darwin':
        print_like_macos(text)
    else:
        raise NotImplementedError("Printing on your platform is currently not supported.")


def print_like_windows(text):
    with open(current_app.config['PRINT_FILE'], 'w') as f:
        f.write(text)
    os.startfile(current_app.config['PRINT_FILE'], "print")


def print_like_linux(text):
    line_printer_process = subprocess.run([PRINTER_PATH_LINUX], stdin=subprocess.PIPE)
    line_printer_process.stdin.write(str.encode(text))


def print_like_macos(text):
    subprocess.run(['lpr'], input=text.encode(), check=True)
