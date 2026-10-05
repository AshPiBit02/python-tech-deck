from datetime import datetime,timezone
from fastapi import APIRouter,HTTPException,status,Depends
from models import Comment,CommentCreate
from routers.posts import POSTS
from routers.users import users_db

router=APIRouter(prefix="/posts/{post_id}/comments",tags=["Comments"])

COMMENTS:dict[int,dict]={}
next_id=1

def ensure_post_exists(post_id:int)->None:
    if post_id not in POSTS:
        raise HTTPException(status_code=404,detail="Post not found")

@router.post("/",response_model=Comment,status_code=status.HTTP_201_CREATED)
def create_comment(post_id:int,payload:CommentCreate):
    global next_id
    ensure_post_exists(post_id)
    if payload.author_id not in users_db:
        raise HTTPException(status_code=404,detail="Author(user) not found")
    comment=Comment(id=next_id,post_id=post_id,created_at=datetime.now(timezone.utc),**payload.model_dump(),)
    COMMENTS[comment.id]=comment
    next_id+=1
    return comment

@router.get("/",response_model=list[Comment])
def list_comments(post_id:int):
    ensure_post_exists(post_id)
    return [c for c in COMMENTS.values() if c.post_id==post_id]

@router.delete("/{comment_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(post_id:int,comment_id:int):
    ensure_post_exists(post_id)
    comment=COMMENTS.get(comment_id)
    if comment is None or comment.post_id!=post_id:
        raise HTTPException(status_code=404,detail="Comment not found")
    del COMMENTS[comment_id]