from passlib.context import CryptContext

pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash_password(password:str)->str:
    return pwd_context.hash(password)

def verify_password(plain_password:str,hased_password:str)->bool:
    return pwd_context.verify(plain_password,hased_password)

h1=hash_password("secretkey")
h2=hash_password("secretkey")

print(h1)
print(h2)
print(verify_password("secretkey",h1))
print(verify_password("secretkey",h2))
print(h1==h2)

print(verify_password("dummykey",h1))

