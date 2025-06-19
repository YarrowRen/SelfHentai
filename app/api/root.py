# app/api/root.py

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def root():
    return {"message": "SelfHentai API is running"}
