from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List
import requests

app = FastAPI()

JSON_SERVER_URL = "http://localhost:5000/beobjeongdong"

class BjdResponse(BaseModel):
    name: str
    status: str 
    code: str = None

@app.get("/법정동코드찾기(전체)", response_model=List[BjdResponse])
async def 전체코드_검색(query: str = Query(..., description="지역 입력")):
    response = requests.get(JSON_SERVER_URL)
    data = response.json()

    results = []
    for item in data:
        # 특수문자 키 처리
        if "\ufeff법정동코드" in item:
            item["법정동코드"] = item.pop("\ufeff법정동코드")
        if query in item["법정동명"]:
            status = "폐지" if item["폐지여부"] == "폐지" else "존재"
            code = item.get("법정동코드")
            results.append(BjdResponse(name=item["법정동명"], status=status, code=code if status == "존재" else None))
    
    if not results:
        return [{"name": query, "status": "검색 결과 없음"}]
    
    return results

@app.get("/법정동코드찾기(5자리)", response_model=List[BjdResponse])
async def 지역구입력(query: str = Query(..., description="지역 입력")):
    response = requests.get(JSON_SERVER_URL)
    data = response.json()

    results = []
    for item in data:
        # 특수문자 키 처리
        if "\ufeff법정동코드" in item:
            item["법정동코드"] = item.pop("\ufeff법정동코드")

        if query in item["법정동명"] and item["폐지여부"] == "존재":
            full_code = item.get("법정동코드")
            code = full_code[:5] if full_code else None
            results.append(BjdResponse(name=item["법정동명"], status="존재", code=code))

    if not results:
        return [{"name": query, "status": "검색 결과 없음"}]

    return results