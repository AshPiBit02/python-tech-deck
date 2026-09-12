from core.config import settings

def verify_admin_key(admin_key:str)->None:
    if admin_key!=settings.admin_secret_key:
        raise ValueError("Invalid admin key!")