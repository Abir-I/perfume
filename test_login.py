import requests

url = "http://127.0.0.1:8000/api/accounts/login/"

data = {
    "email":    "ashrafuzzaman.abir01@gmail.com",
    "password": "Abir@12345"
}

response = requests.post(url, json=data)
print("Status Code:", response.status_code)
try:
    print("Response:", response.json())
except Exception:
    print("Response:", response.text)