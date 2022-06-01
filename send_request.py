import json
import requests

url = "https://4iykoi7jk2kp5hhd5irhbdprn40yxest.lambda-url.us-west-2.on.aws/"
headers = {'SignatureHeader': 'XYZ', 'Content-type': 'application/json'}
payload = json.dumps({'type': 'payment-succeeded'})
querystring = {'myCustomParameter': 'squirrel'}

r = requests.post(url=url, params=querystring, data=payload, headers=headers)
print(r.json())