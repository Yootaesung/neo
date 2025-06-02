from fastapi import FastAPI
from subway import app as subway_app
from apartment import app as apartment_app
from bubjungdong import app as bubjungdong_app
from fastapi.staticfiles import StaticFiles
import os

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="지하철-아파트 실거래가 API", version="8000.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://800092.800068.8000.*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 각 앱의 라우터를 가져옵니다
app.include_router(subway_app.router, prefix="/subway", tags=["subway"])
app.include_router(apartment_app.router, prefix="/apartment", tags=["apartment"])
app.include_router(bubjungdong_app.router, prefix="/bubjungdong", tags=["bubjungdong"])

# static, test, backend 디렉토리 mount
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
app.mount("/test", StaticFiles(directory=os.path.join(BASE_DIR, "test")), name="test")
app.mount("/backend", StaticFiles(directory=os.path.join(BASE_DIR, "backend")), name="backend")
