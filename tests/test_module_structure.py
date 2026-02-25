"""
Tests that verify the module separation:
- cashier.db       — database access layer
- cashier.helpers  — pure utilities, auth, file handling
- cashier.printing — receipt building, printing, customer number
"""


class TestDbModuleExports:
    """cashier.db must export all database-related functions."""

    def test_import_get_db(self):
        from cashier.db import get_db
        assert callable(get_db)

    def test_import_connect_db(self):
        from cashier.db import connect_db
        assert callable(connect_db)

    def test_import_init_db(self):
        from cashier.db import init_db
        assert callable(init_db)

    def test_import_add_item_to_db(self):
        from cashier.db import add_item_to_db
        assert callable(add_item_to_db)

    def test_import_fetch_item_from_db(self):
        from cashier.db import fetch_item_from_db
        assert callable(fetch_item_from_db)

    def test_import_store_transaction(self):
        from cashier.db import store_transaction
        assert callable(store_transaction)

    def test_import_map_items_to_transaction(self):
        from cashier.db import map_items_to_transaction
        assert callable(map_items_to_transaction)


class TestHelpersModuleExports:
    """cashier.helpers must export utility functions and types."""

    def test_import_format_price(self):
        from cashier.helpers import format_price
        assert callable(format_price)

    def test_import_file_allowed(self):
        from cashier.helpers import file_allowed
        assert callable(file_allowed)

    def test_import_optionally_store_image(self):
        from cashier.helpers import optionally_store_image
        assert callable(optionally_store_image)

    def test_import_save_file_to_disk(self):
        from cashier.helpers import save_file_to_disk
        assert callable(save_file_to_disk)

    def test_import_login_required(self):
        from cashier.helpers import login_required
        assert callable(login_required)

    def test_import_new_item(self):
        from cashier.helpers import NewItem
        item = NewItem(title='x', price=1.0, image_link=None, color='#000')
        assert item.title == 'x'

    def test_import_allowed_extensions(self):
        from cashier.helpers import ALLOWED_EXTENSIONS
        assert 'png' in ALLOWED_EXTENSIONS


class TestPrintingModuleExports:
    """cashier.printing must export receipt / printing functions."""

    def test_import_process_receipt(self):
        from cashier.printing import process_receipt
        assert callable(process_receipt)

    def test_import_prepare_receipt(self):
        from cashier.printing import prepare_receipt
        assert callable(prepare_receipt)

    def test_import_build_kitchen_receipt(self):
        from cashier.printing import build_kitchen_receipt
        assert callable(build_kitchen_receipt)

    def test_import_build_customer_receipt(self):
        from cashier.printing import build_customer_receipt
        assert callable(build_customer_receipt)

    def test_import_build_item_listing(self):
        from cashier.printing import build_item_listing
        assert callable(build_item_listing)

    def test_import_print_receipt(self):
        from cashier.printing import print_receipt
        assert callable(print_receipt)

    def test_import_print_like_windows(self):
        from cashier.printing import print_like_windows
        assert callable(print_like_windows)

    def test_import_print_like_linux(self):
        from cashier.printing import print_like_linux
        assert callable(print_like_linux)

    def test_import_print_like_macos(self):
        from cashier.printing import print_like_macos
        assert callable(print_like_macos)

    def test_import_get_customer_number(self):
        from cashier.printing import get_customer_number
        assert callable(get_customer_number)

    def test_import_increase_customer_number_by(self):
        from cashier.printing import increase_customer_number_by
        assert callable(increase_customer_number_by)

    def test_import_customer_number(self):
        import cashier.printing as p
        assert isinstance(p.customer_number, int)

    def test_import_ascii_separator(self):
        from cashier.printing import ASCII_SEPARATOR
        assert isinstance(ASCII_SEPARATOR, str)
        assert '---' in ASCII_SEPARATOR
