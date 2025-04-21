from fastapi import FastAPI, Query, APIRouter, HTTPException
from pymongo.errors import PyMongoError, OperationFailure
from typing import List, Optional
from pydantic import BaseModel
from database import client
from pymongo import MongoClient
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB 연결
try:
    mydb = client["subway"]
    mycol = mydb["subway"]
    bubjungdb = client["bubjungdong"]
    last_search_col = bubjungdb["last_search"]  # 마지막 검색어 컬렉션
    # 데이터베이스 연결 테스트
    logger.info(f"데이터베이스 정보: {client.server_info()}")
    logger.info(f"컬렉션 통계: {mycol.estimated_document_count()} 문서")
except Exception as e:
    logger.error(f"데이터베이스 연결 오류: {str(e)}")
    raise

class SubwayItem(BaseModel):
    """지하철역 정보"""
    subwayOpenDate: str
    subwayName: str
    subwayLocation: str
    subwayLine: str

class SubwayResponse(BaseModel):
    """지하철역 검색 응답"""
    result: bool
    resultCount: int
    results: List[SubwayItem]
    message: str = None

app = FastAPI()
router = APIRouter()

@router.get('/getsubway')
async def GetSubway(
    dong: str = Query(
        None,
        title="법정동",
        description="검색할 법정동명을 입력하세요. 입력하지 않으면 마지막으로 검색한 법정동을 사용합니다.",
        min_length=0,
        required=False
    )
) -> SubwayResponse:
    """지하철역의 정보를 조회하는 API"""
    try:
        # dong이 없으면 마지막 검색어 사용
        if dong is None:
            last_search = last_search_col.find_one({"type": "last_dong"})
            if last_search:
                dong = last_search.get("dong")
            
        if dong is None:
            raise HTTPException(status_code=400, detail="법정동을 입력하세요")
            
        query = {
            "위치": {"$regex": dong, "$options": "i"}
        }
        logger.info(f"검색 쿼리: {query}")
        
        try:
            items = list(mycol.find(query, {"_id": 0, "개통일": 1, "역명": 1, "위치": 1, "소속 노선": 1}))
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f'데이터베이스 조회 실패: {str(e)}') from e
        
        logger.info(f"검색 결과 수: {len(items)}")
        if items:
            logger.info(f"첫 번째 결과: {items[0]}")
        
        if not items:
            return SubwayResponse(
                result=False,
                resultCount=0,
                results=[],
                message=f"'{dong}' 법정동을 찾을 수 없습니다."
            )

        results = []
        for item in items:
            try:
                # 개통일 포맷 변경 (예: "2025년 4월 21일" -> "20250421")
                open_date = item.get("개통일", "")
                formatted_date = ""
                if open_date:
                    # 문자열에서 숫자만 추출
                    formatted_date = ''.join(filter(str.isdigit, open_date))
                    
                    # 8자리가 아닌 경우 빈 문자열 반환
                    if len(formatted_date) != 8:
                        formatted_date = ""
                
                results.append(SubwayItem(
                    subwayOpenDate=formatted_date,
                    subwayName=item.get("역명", ""),
                    subwayLocation=item.get("위치", ""),
                    subwayLine=item.get("소속 노선", "")
                ))
            except ValueError as e:
                logger.error(f"데이터 변환 오류: {str(e)}, 데이터: {item}")
                continue

        return SubwayResponse(
            result=True,
            resultCount=len(results),
            results=results
        )
        
    except HTTPException:
        raise
    except OperationFailure as e:
        raise HTTPException(status_code=500, detail=f'데이터베이스 작업 실패: {str(e)}') from e
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f'데이터베이스 오류: {str(e)}') from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'서버 오류: {str(e)}') from e

@router.get('/getopendate')
async def GetSubwayOpenDate(
    station: str = Query(
        None,
        title="역명",
        description="검색할 지하철역 또는 지역명을 입력하세요. 입력하지 않으면 모든 역의 개통일을 조회합니다.",
        min_length=0,
        required=False
    )
) -> SubwayResponse:
    """지하철역의 개통일을 조회하는 API"""
    try:
        query = {}
        if station:
            query["$or"] = [
                {"역명": {"$regex": station, "$options": "i"}},
                {"위치": {"$regex": station, "$options": "i"}}
            ]

        cursor = mycol.find(query, {"_id": 0})
        stations = list(cursor)

        if not stations:
            return SubwayResponse(
                result=False,
                resultCount=0,
                results=[],
                message="해당하는 역이 없습니다."
            )

        results = []
        for station_data in stations:
            raw_open_date = station_data.get("개통일", "").strip()
            formatted_date = ''.join(filter(str.isdigit, raw_open_date))

            if len(formatted_date) != 8:
                continue

            results.append(
                SubwayItem(
                    subwayOpenDate=formatted_date,
                    subwayName=station_data.get("역명", ""),
                    subwayLocation=station_data.get("위치", ""),
                    subwayLine=station_data.get("소속 노선", "")
                )
            )

        if not results:
            return SubwayResponse(
                result=False,
                resultCount=0,
                results=[],
                message="유효한 개통일이 있는 역을 찾을 수 없습니다."
            )

        return SubwayResponse(
            result=True,
            resultCount=len(results),
            results=results
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

app.include_router(router)
