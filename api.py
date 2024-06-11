import io

from fastapi import Body, Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import auth
import db
import rewe_process

app = FastAPI()
# Configure CORS (Cross-Origin Resource Sharing) settings
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://localhost:8081",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


async def get_user_from_request(request: Request) -> db.User:
    credentials = await auth.get_bearer_credentials(request)
    jwt_data = auth.jwt_decode(credentials.credentials)
    user = db.find_user(jwt_data["sub"])
    return user


# Define an OPTIONS route for CORS preflight requests
@app.options("/api/")
async def options_route():
    return {"methods": "OPTIONS, GET, POST, PUT, DELETE"}


@app.post("/api/login")
async def login(user_data: dict = Body(...)):
    user = db.find_user(user_data["username"], user_data["password"])
    if user is None:
        raise HTTPException(status_code=404, detail="Not found (from FastAPI).")
    token = auth.jwt_encode(user_data["username"])
    return dict(token=token)


@app.post("/api/register")
async def register(user_data: dict = Body(...)):
    if db.find_user(user_data["username"]):
        raise HTTPException(status_code=409)
    db.register(user_data["username"], user_data["password"])
    token = auth.jwt_encode(user_data["username"])
    return JSONResponse(content=dict(token=token), status_code=201)


@app.post("/api/db/clean", dependencies=[Depends(auth.authenticate)])
async def clean_db(request: Request):
    user = await get_user_from_request(request)
    if user.name not in ["zzo", "jthies"]:
        raise HTTPException(status_code=401)
    db.clean()
    db.create_database()


@app.get("/api/bills", dependencies=[Depends(auth.authenticate)])
async def get_bills(request: Request):
    user = await get_user_from_request(request)
    assert user is not None
    data = db.get_bills(user)
    return data


@app.get("/api/charts/daily", dependencies=[Depends(auth.authenticate)])
async def get_daily_data(request: Request):
    user = await get_user_from_request(request)
    assert user is not None
    data = db.retrieve_daily_data(user)
    return data


@app.get("/api/charts/yearly", dependencies=[Depends(auth.authenticate)])
async def get_yearly_data(request: Request):
    user = await get_user_from_request(request)
    assert user is not None
    data = db.retrieve_yearly_data(user)
    return data


@app.post("/api/images", dependencies=[Depends(auth.authenticate)])
async def process_upload_image(file: UploadFile = File(...)):
    raise NotImplementedError("No image processing yet")


@app.post("/api/pdfs", dependencies=[Depends(auth.authenticate)])
async def process_upload_pdf(request: Request, file: UploadFile = File(...)):
    contents = await file.read()
    await file.close()

    user = await get_user_from_request(request)
    with io.BytesIO(contents) as fd:
        bill_id = rewe_process.parse_rewe_ebon(fd, user.id)
    return db.jsonify_bill(bill_id=bill_id)
