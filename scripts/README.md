# Scripts

Use `update-de-data.py` to update the data files for Age of Empires II Definitive Edition and Age of Empires II Return of Rome.

## Setup

Create a Python3 virtual environment with genieutils-py installed:

```shell
python3 -m venv venv
source venv/bin/activate
pip install genieutils-py
```

## Usage

Activate the virtual environment if not already active:

```shell
source venv/bin/activate
```

Then run the script, passing the path to your local installation of Age of Empires II as a parameter:

```shell
./update-de-data.py ~/aoe/Aoe2DE\ proton/
```

Your data files will be updated with the current data.
