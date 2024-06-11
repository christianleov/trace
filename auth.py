import datetime
import os

import jwt
from dotenv import load_dotenv
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer

load_dotenv()
JWT_ALG = "HS256"
JWT_SECRET = os.getenv("JWT_SECRET")


def jwt_encode(user_name):
    exp = datetime.datetime.now() + datetime.timedelta(days=30)
    data = dict(sub=user_name, exp=exp)
    token = jwt.encode(data, JWT_SECRET, algorithm=JWT_ALG)
    return token


def jwt_decode(token):
    data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    return data


async def get_bearer_credentials(request: Request):
    bearer = HTTPBearer()
    credentials = await bearer(request)
    return credentials


async def authenticate(request: Request):
    credentials = await get_bearer_credentials(request)
    if not credentials:
        raise HTTPException(status_code=401)
    if not credentials.scheme == "Bearer":
        raise HTTPException(status_code=401)
    try:
        user_data = jwt_decode(credentials.credentials)
    except jwt.exceptions.InvalidSignatureError:
        raise HTTPException(status_code=401)
    if user_data["exp"] < datetime.datetime.now().timestamp():
        raise HTTPException(status_code=401)
