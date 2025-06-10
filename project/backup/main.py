from fastapi import FastAPI
from bubjungdong import app as bubjungdong_app
from apartment import app as apartment_app
from excluusear import app as excluusear_app
from floor import app as floor_app
from aptprice import app as aptprice_app
from subway import app as subway_app
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="부동산 API", version="1.0.0")

# 각 앱의 라우터를 가져옵니다
app.include_router(bubjungdong_app.router, prefix="/bubjungdong", tags=["bubjungdongCode"])
app.include_router(subway_app.router, prefix="/subway", tags=["subway"])
app.include_router(apartment_app.router, prefix="/apartment", tags=["apartmentName"])
app.include_router(excluusear_app.router, prefix="/excluusear", tags=["excluUseAr"])
app.include_router(floor_app.router, prefix="/floor", tags=["floor"])
app.include_router(aptprice_app.router, prefix="/aptprice", tags=["aptPrice"])

# static 디렉토리 mount
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")