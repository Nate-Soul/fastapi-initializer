from fastapi import FastAPI

from app.database import engine, Base
from app.routes import users

Base.metadata.create_all(bind=engine)

app = FastAPI()

# API ROOT
@app.get("/")
def read_root():
    return {"message", "Welcome to FastAPI Server"}

#routers
app.include_router(users.router)