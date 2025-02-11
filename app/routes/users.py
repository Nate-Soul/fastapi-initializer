from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Annotated, List

#internal modules
from app.database import get_db
from app.models.users import User
from app.schemas.users import UserCreate, UserResponse, UserUpdate
from app.exceptions import raise_not_found_exception, raise_no_content

router = APIRouter(
    tags=["users"],
)

db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: db_dependency):
    db_user = User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users", response_model=List[UserResponse])
def get_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise_not_found_exception(detail="User not found!")
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
def edit_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise_not_found_exception(detail="User not found!")
    db_user.name  = user.name if user.name is not None else db_user.name
    db_user.email = user.email if user.email is not None else db_user.email
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/users/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise_not_found_exception(detail="User not found")

    db.delete(db_user)
    db.commit()
    raise_no_content(detail="User deleted")