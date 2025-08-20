# Work Order Import
This script is used to automate adding accessorial fees for work orders

## Table of Contents
- [Usage](#usage)

## Usage
1. Retrieve new token via APIAuthenticationScript.py (must have Username, Password, and System ID in an .env file to retrieve token). After script is ran, token should appear in your .env file
```bash
python APIAuthenticationScript.py
```

2. Create & Activate a virtual environment:
```bash
python -m venv env
yourenv/Scripts/activate
```

3. Install the dependencies:
```bash
pip install -r requirements.txt
```

4. Run the script
```bash
python invoice.py
```
