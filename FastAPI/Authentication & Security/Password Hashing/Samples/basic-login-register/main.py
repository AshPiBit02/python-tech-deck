from passlib.context import CryptContext

pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash_password(password:str)->str:
    return pwd_context.hash(password)

def verify_password(plain_password:str,hashed_password:str)->bool:
    return pwd_context.verify(plain_password,hashed_password)

USER={}

def register(email:str,password:str)->None:
    hashed_password=pwd_context.hash(password)
    USER[email]=hashed_password
    print("New user registered")

def login(email:str,password:str)->None:
    if email not in USER:
        print({"message":"Unknown user. Register first"})
        return 
    if not verify_password(password,USER[email]):
        print({"message":"Incorrect password!"})
        return
    print({"message":"Login successful"})

register("rhaeneragaeg249@gmail.com","secret125")
register("aegonVthetarge@gmail.com","secret125")

login("aegonVthetarge@gmail.com","secret125")
login("aegonVthee@gmail.com","secret125")
login("aegonVthetarge@gmail.com","secret15")