from fastapi import APIRouter,HTTPException
from pydantic import BaseModel

router=APIRouter(prefix="/posts",tags=["Posts"])

POSTS:dict[int,dict]={
    1:{"id":1,"title":"Hello World","content":"The first post"},
    1:{"id":2,"title":"Statements","content":"The second post"},
    1:{"id":3,"title":"Conditional Statements","content":"The third post"},
}
next_id=4

class PostCreate(BaseModel):
    title:str
    content:str

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
def create_post(body:PostCreate):
    global next_id
    post={"id":next_id,"title":body.title,"content":body.content}
    POSTS[next_id]=post
    next_id+=1
    return post