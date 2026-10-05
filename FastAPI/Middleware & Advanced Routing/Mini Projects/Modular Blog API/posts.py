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
