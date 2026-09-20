from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

User="Dummy Model"

async def get_user_by_id(db:AsyncSession,user_id:int):
    result=await db.execute(select(User)).where(User.id==user_id)
    return result.scalar_one_or_none()

async def get_all_users(db:AsyncSession):
    result=await db.execute(select(User))
    return result.scalars().all()

async def create_user(db:AsyncSession,email:str,hashed_password:str):
    new_user=User(email=email,hashed_password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
