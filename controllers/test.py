import requests

url = "http://localhost:8073/api/auth/token"
headers = {
    "login": "admin@innoving.com",
    "password": "1234",
    "db": "innoving_id30",
    "content-type": "application/jsonp"
}

response = requests.get(url, headers=headers)

print(response.json())