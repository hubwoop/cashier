# cashier
A simple cashier UI that runs in web-browsers

## Getting Started

- Install/Have python3.6 and optionally virtualenv
- Clone repository
- (optional) Create and activate virtualenv
- Create DB: ```sqlite3 /tmp/cashier.db < schema.sql```
- Install requirements: ```pip install -r /path/to/requirements.txt```
- Install cashier ```pip install --editable .```
- export environment variables: FLASK_APP=cashier, FLASK_DEBUG=true
- ```flask run```

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
