from datetime import datetime
from pydantic import BaseModel,EmailStr

class UserCreate(BaseModel):
    username:str
    email:EmailStr

class User(UserCreate):
    id:int

class PostCreate(BaseModel):
    title:str
    content:str
    author_id:int

class Post(PostCreate):
    id:int
    created_at:datetime

class CommentCreate(BaseModel):
    content:str
    author_id:int

class Comment(CommentCreate):
    id:int
    post_id:int
    created_at:datetime