from pydantic_settings import BaseSettings,SettingsConfigDict
from pathlib import Path

BASE_DIR=Path(__file__).resolve().parent.parent
class Settings(BaseSettings):
    db_user:str
    db_password:str
    db_host:str="localhost"
    db_port:str="5432"
    db_name:str
    db_name_test:str|None=None
    testing:bool=False
    algorithm:str
    secret_key:str
    admin_secret_key:str
    pin:str

    @property
    def database_url(self)->str:
        active_db=self.db_name_test if self.testing and self.db_name_test else self.db_name
        return f"postgresql+psycopg2://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{active_db}"

    model_config=SettingsConfigDict(env_file=BASE_DIR/".env")

settings=Settings()