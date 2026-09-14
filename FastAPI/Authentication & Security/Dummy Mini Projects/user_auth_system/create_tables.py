from db.database import Base,engine
from models import User,RefreshToken
print("Creating tables...")
Base.metadata.create_all(bind=engine)