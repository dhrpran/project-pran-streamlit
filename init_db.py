from database import Base, engine
from models import Content


Base.metadata.create_all(bind=engine)
