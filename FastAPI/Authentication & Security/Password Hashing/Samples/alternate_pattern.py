import bcrypt

def hash_password(password:str)->str:
    salt=bcrypt.gensalt()
    hashed=bcrypt.hashpw(password.encode("utf-8"),salt)
    return hashed.decode("utf-8")

def verfy_password(plain_password:str,hashed_password:str)->bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"),hashed_password.encode("utf-8"))

h1=hash_password("secretsecret")
h2=hash_password("secretsecret")

print(h1)
print(h2)

print(verfy_password("secretsecret",h1))
print(verfy_password("secretsecret",h2))
print(verfy_password("wrong",h2))
print(h1==h2)