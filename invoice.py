import requests
from dotenv import load_dotenv
import os

load_dotenv()
user = os.getenv('USERNAME')
passw = os.getenv('PASSWORD')
system_id = os.getenv('SYSTEM_ID')
token = os.getenv('W_TOKEN')

order_adjust = 'https://wms.3plwinner.com/pmomsws/orderadjustment.svc/AddOffer'

#Add a service charge (offer) to an existing order in Veracore
def add_charge(order_number, offer_id, qty=1, price=0.0):
    payload = {
        "AuthenticationHeader": {
            "Username": user,
            "Password": passw
        },
        "AddOfferWSObject": {
            "OrderID": order_number,
            "Comments": f"Added {qty} of {offer_id}",
            "Offers": [
                {
                    "OfferID": offer_id,
                    "Quantity": qty,
                    "Price": price,
                    "OriginalPrice": price,
                    "OrderShipToKey": {"Key": "1"} #usually 1 for single ship-to
                }
            ]
        }
    }

    print(f"--> Sending to Veracore: {payload}")
    response = requests.post(
        order_adjust,
        json=payload,
        timeout=15
    )

    if response.status_code == 200:
        print(f"Successfully Added {offer_id} (x{qty}) to Order {order_number}")
    else:
        print(f"Error {response.status_code}: {response.text}")




def main():
    print("===Veracore Charge Scan Tester===")
    print("Scan an ORDER barcode first, then a CHARGE barcode.")
    print("Type 'exit' to quit.\n")

    while True:
        order_number = input("Scan ORDER barcode: ").strip()
        if order_number.lower() == "exit":
            break
        charge_code = input("Scan CHARGE barcode: ").strip()
        if charge_code.lower() == "exit":
            break

        add_charge(order_number, charge_code, qty=1, price=0.0)

if __name__ == "__main__":
    main()
