import hmac,hashlib,urllib.request

secret_key=b"whsec_test_secret"

body=b'{\"event\":\"payment.succeeded\",\"amount\":5999}'
sig=hmac.new(secret_key,body,hashlib.sha256).hexdigest()
req=urllib.request.Request(
    'http://127.0.0.1:8000/webhooks/payment',
    data=body,
    headers={'X-Signature':sig,'Content-Type':'application/json'},
    method='POST',
)
print(urllib.request.urlopen(req).read())
print("DATA: ",req.data)