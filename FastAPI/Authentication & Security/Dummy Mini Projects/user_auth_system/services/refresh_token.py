from sqlalchemy.orm import Session
from models.refresh_token import RefreshToken

def store_refresh_token(db:Session,token:str,user_id:int)->RefreshToken:
    db_token=RefreshToken(token=token,user_id=user_id)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token

def get_valid_refresh_token(db:Session,token:str)->RefreshToken|None:
    return db.query(RefreshToken).filter(RefreshToken.token==token,RefreshToken.revoked==False).first()

def revoke_refresh_token(db:Session,token:str)->bool:
    db_token=db.query(RefreshToken).filter(RefreshToken.token==token).first()
    if not db_token:
        return False
    db_token.revoked=True
    db.commit()
    return True