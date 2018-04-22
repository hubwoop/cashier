# cashier
A virtual cash register / lightweight POS for devices with web browsers.

## Getting Started

- Install/Have python3.6 and optionally virtualenv
- Clone repository
- Create and activate a virtualenv
- Install requirements: ```pip install -r /path/to/requirements.txt```
- Install cashier. Run in project root: ```pip install --editable .```
- Export environment variables: ```FLASK_APP=cashier```, ```FLASK_DEBUG=true```
- Create DB: ```flask initdb```
- ```flask run```

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
