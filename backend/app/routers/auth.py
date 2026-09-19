from fastapi import APIRouter, Depends, Response

from ..auth import create_token, current_user, verify_password
from ..db import db, serialize
from ..schemas import LoginIn

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(payload: LoginIn, response: Response):
    user = await db().users.find_one({"email": payload.email.lower()})
    if not user or not verify_password(payload.password, user["password_hash"]):
        return Response(status_code=401, content="Invalid credentials")
    token = create_token(user)
    response.set_cookie("access_token", token, httponly=True, samesite="lax")
    return {"user": serialize(user)}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"ok": True}


@router.get("/me")
async def me(user: dict = Depends(current_user)):
    return {"user": user}
