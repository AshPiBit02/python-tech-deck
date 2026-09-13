from fastapi import APIRouter,Depends,HTTPException
from dependencies.db_dependency import database_dependency
from models import User
from schemas.user import UserOut,UserUpdate
from services.user import get_all_users,get_user_by_id,update_user,delete_user
