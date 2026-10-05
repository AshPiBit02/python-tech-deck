from datetime import datetime,timezone
from fastapi import APIRouter,HTTPException,status
from models import Comment,CommentCreate
from routers.posts import POSTS
from routers.users import users_db

router=APIRouter(prefix="/posts/{post_id}/comments",tags=["Comments"])

COMMENTS:dict[int,dict]={}
next_id=1

def ensure_post_exists(post_id:int)->None:
    if post_id not in POSTS:
        raise HTTPException(status_code=404,detail="Post not found")
    