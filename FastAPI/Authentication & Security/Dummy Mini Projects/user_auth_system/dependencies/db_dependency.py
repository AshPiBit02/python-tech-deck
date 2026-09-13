from db.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from typing import Annotated

database_dependency=Annotated[Session,Depends(get_db)]