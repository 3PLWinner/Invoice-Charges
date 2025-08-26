# Work Order Import
This script is used to automate adding accessorial fees for work orders

## Table of Contents
- [Usage](#usage)

## Usage
1. Clone Repository
```bash
git clone https://github.com/3PLWinner/Invoice-Charges.git
```

2. Retrieve new token via APIAuthenticationScript.py (must have Username, Password, and System ID in an .env file to retrieve token). After script is ran, token should appear in your .env file
```bash
python APIAuthenticationScript.py
```

3. Create & Activate a virtual environment:
```bash
python -m venv env
yourenv/Scripts/activate
```

4. Install the dependencies:
```bash
pip install -r requirements.txt
```

5. Run the script
```bash
python invoice.py
```
