from fastapi import APIRouter,HTTPException,status
from datetime import datetime,timezone
from models import Post,PostCreate
from routers.users import users_db

router=APIRouter(prefix="/posts",tags=["Posts"])

POSTS:dict[int,dict]={
}
next_id=1


@router.get("/")
def list_posts():
    return list(POSTS.values())

@router.get("/{post_id}")
def get_post(post_id:int):
    post=POSTS.get(post_id)
    if not post:
        raise HTTPException(status_code=404,detail=f"Post with id '{post_id}'not found!")
    return post

@router.post("/",status_code=201)
def create_post(payload:PostCreate):
    global next_id
    if payload.author_id not in users_db:
        raise HTTPException(status_code=404,detail="Author(user) not found")
    post=Post(id=next_id,created_at=datetime.now(timezone.utc),**payload.model_dump())
    POSTS[post.id]=post
    next_id+=1
    return post

@router.delete("/{post_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id:int):
    if post_id not in POSTS:
        raise HTTPException(status_code=404,detail="Post not found")
    del POSTS[post_id]
