# cashier
A virtual cash register / lightweight POS for devices with web browsers.

> **Local use only.** This app is designed to run on a local network and must not be exposed to the internet.

## Install

```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install --editable .
```

## Run

```sh
export FLASK_APP=cashier
flask initdb   # first time only
flask run
```

## Test

```sh
pip install pytest
python -m pytest tests/
```

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
