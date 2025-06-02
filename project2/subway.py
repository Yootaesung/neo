import json
import httpx
from fastapi import FastAPI, Query, APIRouter, HTTPException, Depends
from typing import Dict, Optional
from pydantic import BaseModel
from pymongo.errors import PyMongoError, OperationFailure
from database import client
from datetime import datetime

class SubwayItem(BaseModel):
    """지하철역 정보"""
    stationName: str
    location: str
    openDate: str

app = FastAPI()
router = APIRouter()

@router.get('/getsubway')
async def GetSubway(
    station: str = Query(
        None,
        title="검색어",
        description="검색할 지하철역 또는 지역명을 입력하세요. (입력하지 않으면 이전에 입력한 값이 자동으로 사용)",
        min_length=0,
        required=False
    )
) -> Dict:
    try:
        mydb = client["subway"]
        subway_col = mydb["subway"]
        # 검색 쿼리 생성
        query = {
            "$or": [
                {"역명": {"$regex": station, "$options": "i"}},
                {"위치": {"$regex": station, "$options": "i"}}
            ]
        } if station else {}
        results = []
        for doc in subway_col.find(query):
            import re
            open_date = doc.get("개통일", "")
            formatted_date = ""
            if open_date:
                # 다양한 포맷 시도
                # 1. YYYY-MM-DD, YYYY.MM.DD, YYYY/MM/DD 등
                m = re.match(r"(\d{4})[-./](\d{2})[-./](\d{2})", open_date)
                if m:
                    formatted_date = f"{m.group(1)}{m.group(2)}{m.group(3)}"
                else:
                    # 2. YYYY년 MM월 DD일
                    m = re.match(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", open_date)
                    if m:
                        formatted_date = f"{m.group(1)}{int(m.group(2)):02d}{int(m.group(3)):02d}"
                    else:
                        # 3. YYYYMMDD (이미 숫자만)
                        digits = ''.join(filter(str.isdigit, open_date))
                        if len(digits) == 8:
                            formatted_date = digits
                        else:
                            # 4. YYYY-MM-DD HH:MM:SS 등
                            m = re.match(r"(\d{4})[-./](\d{2})[-./](\d{2})", open_date)
                            if m:
                                formatted_date = f"{m.group(1)}{m.group(2)}{m.group(3)}"
                            else:
                                formatted_date = ""
            # 위치(행정구역명)로 법정동코드 조회
            try:
                url = "http://localhost:8000/bubjungdong/getbubjungdongcode"
                params = {"location": doc["위치"]}
                bubjungdongCode = None
                async with httpx.AsyncClient() as async_client:
                    resp = await async_client.get(url, params=params)
                    data = resp.json()
                    print(f"법정동코드 API 응답: {data}")
                    if data.get("result"):
                        bubjungdongCode = data["bubjungdongCode"]
            except Exception as e:
                print(f"법정동코드 조회 에러: {e}")
                bubjungdongCode = None
            results.append({
                "stationName": doc["역명"],
                "location": doc["위치"],
                "openDate": formatted_date,
                "bubjungdongCode": bubjungdongCode,
                "stationRoadAddress": doc.get("역사도로명주소", "")
            })
        return {
            "result": bool(results),
            "resultCount": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(router)
