import requests
import base64
import datetime
from requests.auth import HTTPBasicAuth


#! MPESA Credentials
BUSINESS_SHORTCODE = "174379"
LIPA_NA_MPESA_PASSKEY = "YOUR_PASSKEY"
CONSUMER_KEY = "CONSUMER_KEY"
CONSUMER_SECRET = "CONSUMER_SECRET"
CALLBACK_URL = "YOUR_CALLBACK_URL"

#! Get access token
def get_access_token():
    print("Inside get_access_token()")  # Debugging print

    auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    try:
        print(" Sending request to:", auth_url)

        response = requests.get(auth_url, auth=(CONSUMER_KEY, CONSUMER_SECRET), timeout=10)

        print(f" Response Status Code: {response.status_code}")  # Show HTTP response code
        print(f"Raw Response Text: {response.text}")  # Show full response content

        response_json = response.json()
        access_token = response_json.get("access_token")

        if access_token:
            print("Access Token Retrieved Successfully!")
        else:
            print("⚠️ No Access Token Found in Response!")

        return access_token

    except requests.exceptions.Timeout:
        print("Request Timed Out! Check Your Internet Connection.")
    except requests.exceptions.RequestException as e:
        print("Request Failed:", str(e))

    return None

#! Generate password for STK Push
def generate_password():
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    password = f"{BUSINESS_SHORTCODE}{LIPA_NA_MPESA_PASSKEY}{timestamp}"
    return base64.b64encode(password.encode()).decode()

#! STK Push Request
def stk_push(phone_number, amount, order_id):
    access_token = get_access_token()

    # Check if token retrieval failed
    if isinstance(access_token, dict) and "error" in access_token:
        return access_token

    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    payload = {
        "BusinessShortCode": BUSINESS_SHORTCODE,
        "Password": generate_password(),
        "Timestamp": datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": BUSINESS_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": str(order_id),
        "TransactionDesc": "Payment for service"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "STK Push request failed", "details": response.text}

