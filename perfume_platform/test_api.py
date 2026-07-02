import requests

url = "http://127.0.0.1:8000/api/accounts/register/"

data = {
    "first_name": "Ashrafuzzaman",
    "last_name": "Abir",
    "email": "ashrafuzzaman.abir01@gmail.com",
    "password": "Abir@12345",
    "phone": "01712345678"
}

response = requests.post(url, json=data)

print("Status Code:", response.status_code)

# this prints just the key part of the error instead of the whole HTML page
if response.status_code != 201:
    from bs4 import BeautifulSoup
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        # Django error pages put the actual error in an <pre> or <h1> tag
        error = soup.find('pre') or soup.find('h1') or soup.find('title')
        print("Error:", error.text.strip() if error else response.text[:500])
    except:
        print(response.text[:500])
else:
    print(response.json())