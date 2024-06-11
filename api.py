import datetime
import io
from typing import Optional

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


def __last_day_of_month(start: datetime.date):
    # The day 28 exists in every month. 4 days later, it's always next month.
    # Subtracting the number of the current day brings us back one month.
    next_month = start.replace(day=28) + datetime.timedelta(days=4)
    return next_month - datetime.timedelta(days=next_month.day)


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


@app.get("/api/charts/daily/", dependencies=[Depends(auth.authenticate)])
async def get_daily_data(
    request: Request, month: Optional[int] = None, year: Optional[int] = None
):
    user = await get_user_from_request(request)
    assert user is not None
    if month is None or year is None:
        stop = datetime.datetime.now().date()
        start = stop - datetime.timedelta(days=30)
    else:
        try:
            start = datetime.date(year, month, 1)
            stop = __last_day_of_month(start)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid year or month provided."
            )
    dt = datetime.timedelta(days=1)
    data = db.retrieve_sum_expenses(user, start, stop, dt)
    return data


@app.get("/api/charts/monthly", dependencies=[Depends(auth.authenticate)])
async def get_monthly_data(request: Request, year: Optional[int] = None):
    user = await get_user_from_request(request)
    assert user is not None
    if year is None:
        stop = datetime.datetime.now()
        start = stop - datetime.timedelta(days=365)
    else:
        assert year >= 0
        assert year <= 9999
        start = datetime.date(year, 1, 1)
        stop = datetime.date(year, 12, 31)
    dt = datetime.timedelta(days=30)
    data = db.retrieve_sum_expenses(user, start, stop, dt)
    return data


@app.get("/api/charts/yearly", dependencies=[Depends(auth.authenticate)])
async def get_yearly_data(request: Request):
    user = await get_user_from_request(request)
    assert user is not None
    stop = datetime.date(datetime.datetime.today().year, 1, 1)
    start = stop - datetime.timedelta(days=5 * 365)
    dt = datetime.timedelta(months=1)
    data = db.retrieve_sum_expenses(user, start, stop, dt)
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
