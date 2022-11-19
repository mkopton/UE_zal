"""Advanced programming project, created by Marcin Koptoń"""

from typing import Union
from datetime import datetime
from math import sqrt
from io import BytesIO
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from PIL import Image, ImageOps
from pydantic import BaseModel
import uvicorn

users_db = {
    "marcin": {
        "username": "marcin",
        "full_name": "Marcin Kopton",
        "email": "marcin.kopton@uekat.edu.pl",
        "hashed_password": "hashedsekretnehaslo",
        "disabled": False,
    }
}

app = FastAPI()

def hash_password(password: str):
    """Function to hash password"""
    return "hashed" + password


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class User(BaseModel):
    """Class to hold user info"""
    username: str
    email: Union[str, None] = None
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None


class UserInDB(User):
    """Class to hold user hashed password"""
    hashed_password: str


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return 0


def decode_token(token):
    # This doesn't provide any security at all
    # Check the next version
    user = get_user(users_db, token)
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}


@app.get("/gettime")
async def get_time(User = Depends(get_current_active_user)):
    return datetime.now()

@app.get("/")
def welcome():
    """Function to print welcome message"""
    return {'message': f"Projekt na zaliczenie Programowania Zaawansowanego, sprawdź http://127.0.0.1:8000/docs aby dowiedzieć się więcej!"}

@app.get("/prime/{number}")
def is_prime(number):
    """Function to verify if number is prime"""
    if number.isnumeric() is True:
        verifiednumber = int(number)
        if verifiednumber <= 1:
            return {'message': f"Number {verifiednumber} is not a prime!"}
        for i in range(2, int(sqrt(verifiednumber))+1):
            if verifiednumber % i == 0:
                return {'message': f"Number {verifiednumber} is not a prime!"}

        return {'message': f"Number {verifiednumber} is a prime!"}
    return {'message': f"String {number} is not a valid number!"}

@app.post("/picture/invert")
def image_color_invert(img: UploadFile = File(...)):
    original_image = Image.open(img.file)
    original_image = ImageOps.invert(original_image)
    inverted_image = BytesIO()
    original_image.save(inverted_image, "JPEG")
    inverted_image.seek(0)
    return StreamingResponse(inverted_image, media_type="image/jpeg")

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, log_level="info")
