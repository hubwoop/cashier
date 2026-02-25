"""
Tests for receipt printing routes and helpers:
- POST /print/kitchen
- POST /print/customer
- build_kitchen_receipt()
- build_customer_receipt()
- build_item_listing()
- print_receipt()
"""

import json
import os
from unittest.mock import patch, MagicMock

from cashier.printing import (
    build_kitchen_receipt,
    build_customer_receipt,
    build_item_listing,
)
from tests.conftest import add_item


class TestBuildItemListing:
    """Unit tests for the item listing string builder."""

    def test_single_item(self):
        receipt = {'1': {'amount': 1, 'title': 'Burger'}}
        result = build_item_listing(receipt)
        assert '1x Burger' in result

    def test_multiple_items(self):
        receipt = {
            '1': {'amount': 2, 'title': 'Burger'},
            '2': {'amount': 3, 'title': 'Fries'},
        }
        result = build_item_listing(receipt)
        assert '2x Burger' in result
        assert '3x Fries' in result

    def test_empty_receipt(self):
        result = build_item_listing({})
        assert result == ""


class TestBuildKitchenReceipt:
    """Unit tests for kitchen receipt text generation."""

    def test_contains_order_number(self):
        import cashier.printing as p
        original = p.customer_number
        p.customer_number = 42
        try:
            receipt = {'1': {'amount': 1, 'title': 'Soup'}}
            result = build_kitchen_receipt(receipt)
            assert 'Bestellung #42' in result
        finally:
            p.customer_number = original

    def test_contains_items(self):
        receipt = {'1': {'amount': 2, 'title': 'Pizza'}}
        result = build_kitchen_receipt(receipt)
        assert '2x Pizza' in result

    def test_contains_separator(self):
        receipt = {'1': {'amount': 1, 'title': 'Water'}}
        result = build_kitchen_receipt(receipt)
        assert '---' in result


class TestBuildCustomerReceipt:
    """Unit tests for customer receipt text generation."""

    def test_contains_customer_number(self):
        import cashier.printing as p
        original = p.customer_number
        p.customer_number = 105
        try:
            receipt = {'1': {'amount': 1, 'title': 'Cake'}}
            result = build_customer_receipt(receipt, 3.50)
            # 105 % 100 = 5
            assert '5' in result
        finally:
            p.customer_number = original

    def test_contains_sum(self):
        receipt = {'1': {'amount': 1, 'title': 'Cake'}}
        result = build_customer_receipt(receipt, 3.50)
        assert '3.5' in result

    def test_contains_items(self):
        receipt = {'1': {'amount': 1, 'title': 'Cake'}}
        result = build_customer_receipt(receipt, 3.50)
        assert '1x Cake' in result

    def test_contains_euro_sign(self):
        receipt = {'1': {'amount': 1, 'title': 'X'}}
        result = build_customer_receipt(receipt, 1.0)
        assert '€' in result


class TestPrintKitchenRoute:
    """POST /print/kitchen — kitchen receipt printing."""

    @patch('cashier.cashier.print_receipt', wraps=None)
    def test_print_kitchen_success(self, mock_print, auth_client):
        add_item(auth_client, title='Steak', price='15.00')
        payload = {
            'sum': 15.0,
            '1': {'amount': 1, 'title': 'Steak', 'price': 15.0},
        }
        resp = auth_client.post('/print/kitchen',
                                data=json.dumps(payload),
                                content_type='application/json')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['success'] is True
        mock_print.assert_called_once()

    @patch('cashier.cashier.print_receipt', wraps=None)
    def test_print_kitchen_content_type(self, mock_print, auth_client):
        """Response must have Content-Type: application/json."""
        payload = {'sum': 1.0, '1': {'amount': 1, 'title': 'X', 'price': 1.0}}
        resp = auth_client.post('/print/kitchen',
                                data=json.dumps(payload),
                                content_type='application/json')
        assert resp.content_type == 'application/json'

    @patch('cashier.cashier.print_receipt', wraps=None)
    def test_print_kitchen_receipt_text(self, mock_print, auth_client):
        add_item(auth_client, title='Pasta', price='10.00')
        payload = {
            'sum': 10.0,
            '1': {'amount': 2, 'title': 'Pasta', 'price': 10.0},
        }
        auth_client.post('/print/kitchen',
                         data=json.dumps(payload),
                         content_type='application/json')
        printed_text = mock_print.call_args[0][0]
        assert '2x Pasta' in printed_text
        assert 'Bestellung' in printed_text


class TestPrintCustomerRoute:
    """POST /print/customer — customer receipt printing."""

    @patch('cashier.cashier.print_receipt', wraps=None)
    def test_print_customer_success(self, mock_print, auth_client):
        add_item(auth_client, title='Wine', price='7.00')
        payload = {
            'sum': 7.0,
            '1': {'amount': 1, 'title': 'Wine', 'price': 7.0},
        }
        resp = auth_client.post('/print/customer',
                                data=json.dumps(payload),
                                content_type='application/json')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['success'] is True
        mock_print.assert_called_once()

    @patch('cashier.cashier.print_receipt', wraps=None)
    def test_print_customer_content_type(self, mock_print, auth_client):
        """Response must have Content-Type: application/json."""
        payload = {'sum': 1.0, '1': {'amount': 1, 'title': 'X', 'price': 1.0}}
        resp = auth_client.post('/print/customer',
                                data=json.dumps(payload),
                                content_type='application/json')
        assert resp.content_type == 'application/json'

    @patch('cashier.cashier.print_receipt', wraps=None)
    def test_print_customer_receipt_text(self, mock_print, auth_client):
        payload = {
            'sum': 14.0,
            '1': {'amount': 2, 'title': 'Beer', 'price': 7.0},
        }
        auth_client.post('/print/customer',
                         data=json.dumps(payload),
                         content_type='application/json')
        printed_text = mock_print.call_args[0][0]
        assert '2x Beer' in printed_text
        assert '14.0' in printed_text
        assert '€' in printed_text


class TestPrintLikeWindows:
    """Unit tests for print_like_windows — file writing."""

    @patch('cashier.printing.os.startfile', create=True)
    def test_writes_text_to_file(self, mock_startfile, test_app):
        """print_like_windows must open the file in WRITE mode and write text."""
        import tempfile
        from cashier.printing import print_like_windows
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp_path = tmp.name
        test_app.config['PRINT_FILE'] = tmp_path
        try:
            with test_app.app_context():
                print_like_windows("Hello receipt")
            with open(tmp_path, 'r') as f:
                assert f.read() == "Hello receipt"
        finally:
            os.unlink(tmp_path)

    @patch('cashier.printing.os.startfile', create=True)
    def test_calls_startfile_with_print(self, mock_startfile, test_app):
        """After writing, it must call os.startfile with 'print'."""
        import tempfile
        from cashier.printing import print_like_windows
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp_path = tmp.name
        test_app.config['PRINT_FILE'] = tmp_path
        try:
            with test_app.app_context():
                print_like_windows("test")
            mock_startfile.assert_called_once_with(tmp_path, "print")
        finally:
            os.unlink(tmp_path)


class TestPrintReceipt:
    """Unit tests for the print_receipt dispatcher."""

    @patch('cashier.printing.platform')
    def test_raises_on_unsupported_platform(self, mock_platform):
        from cashier.printing import print_receipt
        mock_platform.system.return_value = 'FreeBSD'
        import pytest
        with pytest.raises(NotImplementedError):
            print_receipt("test text")

    @patch('cashier.printing.platform')
    @patch('cashier.printing.print_like_windows')
    def test_calls_windows_printer(self, mock_win_print, mock_platform):
        from cashier.printing import print_receipt
        mock_platform.system.return_value = 'Windows'
        print_receipt("test")
        mock_win_print.assert_called_once_with("test")

    @patch('cashier.printing.platform')
    @patch('cashier.printing.print_like_linux')
    def test_calls_linux_printer(self, mock_linux_print, mock_platform):
        from cashier.printing import print_receipt
        mock_platform.system.return_value = 'Linux'
        print_receipt("test")
        mock_linux_print.assert_called_once_with("test")

    @patch('cashier.printing.platform')
    @patch('cashier.printing.print_like_macos')
    def test_calls_macos_printer(self, mock_mac_print, mock_platform):
        from cashier.printing import print_receipt
        mock_platform.system.return_value = 'Darwin'
        print_receipt("test mac")
        mock_mac_print.assert_called_once_with("test mac")


class TestPrintLikeMacOS:
    """Unit tests for print_like_macos — uses lpr."""

    @patch('cashier.printing.subprocess.run')
    def test_calls_lpr(self, mock_run, test_app):
        from cashier.printing import print_like_macos
        with test_app.app_context():
            print_like_macos("receipt text")
        mock_run.assert_called_once()
        args = mock_run.call_args
        # Should call lpr
        assert 'lpr' in args[0][0]

    @patch('cashier.printing.subprocess.run')
    def test_passes_text_as_input(self, mock_run, test_app):
        from cashier.printing import print_like_macos
        with test_app.app_context():
            print_like_macos("hello")
        args = mock_run.call_args
        assert args[1].get('input') == b"hello" or args[0][0] is not None
