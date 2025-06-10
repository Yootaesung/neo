from fastapi import FastAPI, Query, APIRouter, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel
from pymongo.errors import PyMongoError, OperationFailure
from pymongo import MongoClient
import os
import json
from datetime import datetime

with open(os.path.join(os.path.dirname(__file__), '../secret.json')) as f:
    secrets = json.load(f)

# Atlas 접속 정보로 MongoClient 생성
ATLAS_HOST = secrets["ATLAS_Hostname"].rstrip('/')
ATLAS_USER = secrets["ATLAS_Username"]
ATLAS_PASS = secrets["ATLAS_Password"]
MONGO_URI = f"mongodb+srv://{ATLAS_USER}:{ATLAS_PASS}@{ATLAS_HOST}/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)

class BubjungdongItem(BaseModel):
    bubjungdongCode: str
    bubjungdongName: str
    exitOrNot: str

app = FastAPI()
router = APIRouter()
routeurl = "http://localhost:8000/bubjungdong/getbubjungdongcode"

@router.get('/getbubjungdongcode')
async def GetBubjungdongCode(
    location: str = Query(
        ..., title="행정구역명", description="예: 서울특별시 강남구"
    )
) -> Dict:
    try:
        mydb = client["bubjungdong"]
        mycol = mydb["bubjungdong"]
        orig_location = location
        # 1. 부분일치(정규식) + 폐지여부: 존재
        query = {"법정동명": {"$regex": f"^{location}", "$options": "i"}, "폐지여부": "존재"}
        items = list(mycol.find(query, {"_id": 0, "법정동코드": 1, "법정동명": 1, "폐지여부": 1}))
        if not items:
            # 2. 완전일치(구 단위) + 폐지여부: 존재
            query = {"법정동명": location, "폐지여부": "존재"}
            items = list(mycol.find(query, {"_id": 0, "법정동코드": 1, "법정동명": 1, "폐지여부": 1}))
        if not items:
            # 3. 포함 검색(존재)
            query = {"법정동명": {"$regex": location, "$options": "i"}, "폐지여부": "존재"}
            items = list(mycol.find(query, {"_id": 0, "법정동코드": 1, "법정동명": 1, "폐지여부": 1}))
        # 4. location 값이 너무 짧으면(구/동만) 시/도 자동 보정
        if not items and ("구" in location or "동" in location) and not ("서울" in location or "경기" in location or "인천" in location or "부산" in location or "대구" in location or "광주" in location or "대전" in location or "울산" in location or "세종" in location or "강원" in location or "충북" in location or "충남" in location or "전북" in location or "전남" in location or "경북" in location or "경남" in location or "제주" in location):
            # 서울특별시를 기본값으로 붙여서 재시도 (실제 서비스라면 구/동별 시도 매핑 필요)
            location = f"서울특별시 {location}"
            query = {"법정동명": {"$regex": f"^{location}", "$options": "i"}, "폐지여부": "존재"}
            items = list(mycol.find(query, {"_id": 0, "법정동코드": 1, "법정동명": 1, "폐지여부": 1}))
            if not items:
                query = {"법정동명": location, "폐지여부": "존재"}
                items = list(mycol.find(query, {"_id": 0, "법정동코드": 1, "법정동명": 1, "폐지여부": 1}))
            if not items:
                query = {"법정동명": {"$regex": location, "$options": "i"}, "폐지여부": "존재"}
                items = list(mycol.find(query, {"_id": 0, "법정동코드": 1, "법정동명": 1, "폐지여부": 1}))
            location = orig_location
        # 공백 제거 후 완전일치 fallback
        if not items:
            def normalize(s):
                return s.replace(" ", "")
            all_items = list(mycol.find({"폐지여부": "존재"}))
            for item in all_items:
                if normalize(item["법정동명"]) == normalize(location):
                    items = [item]
                    break
        print(f"[DEBUG] location={location}")
        print(f"[DEBUG] items={items}")
        if items:
            item = sorted(items, key=lambda x: len(x["법정동명"]), reverse=True)[0]
            code5 = str(item["법정동코드"])[:5]
            print(f"[DEBUG] 반환: {{'result': True, 'bubjungdongCode': {code5}, 'bubjungdongName': {item['법정동명']}}}")
            return {"result": True, "bubjungdongCode": code5, "bubjungdongName": item["법정동명"]}
        else:
            print(f"[DEBUG] 반환: {{'result': False, 'message': '법정동명을 찾을 수 없습니다.'}}")
            return {"result": False, "message": "법정동명을 찾을 수 없습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====== 진단용: DB에 '서울특별시 강남구'가 실제로 존재하는지 확인 ======
if __name__ == "__main__":
    from pymongo import MongoClient
    test_client = MongoClient("mongodb://localhost:27017")  # 실제 환경에 맞게 수정 필요
    mydb = test_client["bubjungdong"]
    mycol = mydb["bubjungdong"]
    result = list(mycol.find({"법정동명": "서울특별시 강남구", "폐지여부": "존재"}))
    print("[DB 진단 결과]", result)

app.include_router(router)
