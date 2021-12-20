
  
import requests
import json

URL = "{baseURL}/admin/healthcheck"

print("Search by Username:")
user = input("> ")
queryURL = URL + f"?username={user}"
response = requests.get(queryURL)
#εναλλακτικά με παράμετρο για authenticication: 
#requests.get(
#  'queryURL', 
#  auth=HTTPBasicAuth('username', 'password')
#)
if (response.status_code == 200):
    print("The request was a success!")
    # Code here will only run if the request is successful
elif (response.status_code == 404:
    print("Result not found!")
    # Code here will react to failed requests
      
userdata = json.loads(response.text)[0]

name = userdata["name"]
email = userdata["email"]
phone = userdata["phone"]

print(f"{name} can be reached via the following methods:")
print(f"Email: {email}")
print(f"Phone: {phone}")
