import json
from fastapi import FastAPI, Query, APIRouter, HTTPException, Depends
from typing import Dict, Optional
from pydantic import BaseModel
from pymongo.errors import PyMongoError, OperationFailure
from dependencies import get_common_params, CommonParams
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
    ),
    common_params: CommonParams = Depends(get_common_params)
) -> Dict:
    try:
        # MongoDB 연결
        mydb = client["subway"]
        subway_col = mydb["subway"]
        bubjungdb = client["bubjungdong"]
        last_search_col = bubjungdb["last_search"]

        # 검색어 설정
        search_term = station
        if not station:
            # 마지막 검색어 가져오기
            last_search = last_search_col.find_one({"type": "last_dong"})
            if last_search and "dong" in last_search:
                search_term = last_search["dong"]

        if not search_term:
            return {
                "result": False,
                "resultCount": 0,
                "message": "검색어를 입력하세요."
            }

        # 검색 쿼리 생성
        query = {
            "$or": [
                {"역명": {"$regex": search_term, "$options": "i"}},
                {"위치": {"$regex": search_term, "$options": "i"}}
            ]
        }

        # 데이터 조회
        results = []
        for doc in subway_col.find(query):
            # 개통일 포맷 변경 (예: "2025년 4월 21일" -> "20250421")
            open_date = doc.get("개통일", "")
            formatted_date = ""
            if open_date:
                # 문자열에서 숫자만 추출
                formatted_date = ''.join(filter(str.isdigit, open_date))
                # 8자리가 아닌 경우 빈 문자열 반환
                if len(formatted_date) != 8:
                    formatted_date = ""

            results.append({
                "stationName": doc["역명"],
                "location": doc["위치"],
                "openDate": formatted_date
            })

        if not results:
            return {
                "result": False,
                "resultCount": 0,
                "message": "검색 결과가 없습니다."
            }

        return {
            "result": True,
            "resultCount": len(results),
            "results": results
        }
        
    except HTTPException:
        raise
    except OperationFailure as e:
        raise HTTPException(status_code=500, detail=f'데이터베이스 작업 실패: {str(e)}') from e
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f'데이터베이스 오류: {str(e)}') from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'서버 오류: {str(e)}') from e

app.include_router(router)
