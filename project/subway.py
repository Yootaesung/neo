from fastapi import FastAPI, Query, APIRouter, HTTPException
from database import client
from typing import List, Optional
from pydantic import BaseModel
from pymongo.errors import PyMongoError, OperationFailure
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

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
    """지하철 정보"""
    subwayOpenDate: str
    subwayName: str
    subwayLocation: str
    subwayLine: str

class SubwayResponse(BaseModel):
    """지하철 검색 응답"""
    result: bool
    resultCount: int
    results: List[SubwayItem]

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
):
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
        
        # 전체 문서 수 확인
        total_docs = mycol.estimated_document_count()
        logger.info(f"전체 문서 수: {total_docs}")
        
        # 샘플 문서 확인
        sample_doc = mycol.find_one()
        logger.info(f"샘플 문서: {sample_doc}")
        
        items = list(mycol.find(query, {"_id": 0, "개통일": 1, "역명": 1, "위치": 1, "소속 노선": 1}))
        logger.info(f"검색 결과 수: {len(items)}")
        if items:
            logger.info(f"첫 번째 결과: {items[0]}")
        
        if not items:
            return SubwayResponse(
                result=False,
                resultCount=0,
                results=[]
            )

        results = []
        for item in items:
            try:
                subway_item = SubwayItem(
                    subwayOpenDate=item.get("개통일", ""),
                    subwayName=item.get("역명", ""),
                    subwayLocation=item.get("위치", ""),
                    subwayLine=item.get("소속 노선", "")
                )
                results.append(subway_item)
            except Exception as e:
                logger.error(f"데이터 변환 오류: {str(e)}, 데이터: {item}")
                continue

        return SubwayResponse(
            result=True,
            resultCount=len(results),
            results=results
        )
        
    except OperationFailure as e:
        logger.error(f"MongoDB 작업 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"데이터베이스 작업 실패: {str(e)}") from e
    except PyMongoError as e:
        logger.error(f"MongoDB 오류: {str(e)}")
        raise HTTPException(status_code=503, detail="데이터베이스 연결 오류") from e
    except Exception as e:
        logger.error(f"예상치 못한 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}") from e

@router.get('/getopendate')
async def GetSubwayOpenDate(
    station: str = Query(
        None,
        title="역명",
        description="검색할 지하철역 이름을 입력하세요. 입력하지 않으면 모든 역의 개통일을 조회합니다.",
        min_length=0,
        required=False
    )
):
    try:
        if station:
            # 특정 역 검색 (부분 일치)
            query = {
                "역명": {"$regex": station, "$options": "i"}
            }
            items = list(mycol.find(query, {"_id": 0, "개통일": 1, "역명": 1, "위치": 1, "소속 노선": 1}))
        else:
            # 모든 역 검색
            items = list(mycol.find({}, {"_id": 0, "개통일": 1, "역명": 1, "위치": 1, "소속 노선": 1}))
        
        if not items:
            return SubwayResponse(
                result=False,
                resultCount=0,
                results=[]
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

        # 역명 기준으로 정렬
        results.sort(key=lambda x: x.subwayName)

        return SubwayResponse(
            result=True,
            resultCount=len(results),
            results=results
        )
        
    except OperationFailure as e:
        logger.error(f"MongoDB 작업 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"데이터베이스 작업 실패: {str(e)}") from e
    except PyMongoError as e:
        logger.error(f"MongoDB 오류: {str(e)}")
        raise HTTPException(status_code=503, detail="데이터베이스 연결 오류") from e
    except Exception as e:
        logger.error(f"예상치 못한 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}") from e

app.include_router(router)
