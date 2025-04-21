from fastapi import FastAPI, Query, APIRouter
from database import client
from typing import List
from pydantic import BaseModel

app = FastAPI()

mydb = client["bubjungdong"]
mycol = mydb["bubjungdong"]

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
