from fastapi import FastAPI, Query, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from database import client
from typing import List
from pydantic import BaseModel
import datetime

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# Static 파일 마운트
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

mydb = client["bubjungdong"]
mycol = mydb["bubjungdong"]
last_search_col = mydb["last_search"]  # 마지막 검색어 저장용 컬렉션

class BubjungdongItem(BaseModel):
    """법정동 정보"""
    bubjungdongCode: str
    bubjungdongName: str
    exitOrNot: str

class BubjungdongResponse(BaseModel):
    """법정동 검색 응답"""
    result: bool
    resultCount: int
    results: List[BubjungdongItem]

router = APIRouter()

@router.get('/getbubjungdong')
async def GetBubjungdong(
    dong: str = Query(
        None,
        title="법정동",
        description="검색할 법정동명을 입력하세요",
        min_length=1
    )
):
    if dong is None:
        return {"오류": "법정동을 입력하세요"}
    query = {
        "법정동명": {"$regex": dong, "$options": "i"},
        "폐지여부": {"$ne": "폐지"}
    }
    items = list(mycol.find(query, {"_id": 0, "법정동코드": 1, "법정동명": 1, "폐지여부": 1}))
    if items:
        # 검색 결과가 있으면 마지막 검색어 저장
        last_search_col.update_one(
            {"type": "last_dong"},
            {
                "$set": {
                    "dong": dong,
                    "timestamp": datetime.datetime.now()
                }
            },
            upsert=True
        )
        
        response = BubjungdongResponse(
            result=True,
            resultCount=len(items),
            results=[
                BubjungdongItem(
                    bubjungdongCode=str(item["법정동코드"])[:5],
                    bubjungdongName=item["법정동명"],
                    exitOrNot=item["폐지여부"]
                ) for item in items
            ]
        )
        return response
    return BubjungdongResponse(
        result=False,
        resultCount=0,
        results=[]
    )

app.include_router(router)
