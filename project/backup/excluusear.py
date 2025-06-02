import json
import requests
import os.path
import xml.etree.ElementTree as ET
from fastapi import FastAPI, Query, APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from datetime import datetime, timedelta
from dependencies import get_common_params, update_common_params, CommonParams
from database import client

BASE_DIR = os.path.dirname(os.path.abspath(os.path.relpath("./")))
secret_file = os.path.join(BASE_DIR, 'secret.json')

def get_secret(setting):
    """비밀 변수를 가져오는 함수"""
    with open(secret_file) as f:
        secrets = json.loads(f.read())
    try:
        return secrets[setting]
    except KeyError:
        errorMsg = "Set the {} environment variable.".format(setting)
        return errorMsg

# MongoDB 연결
mydb = client["apartment"]
last_search_col = mydb["last_search"]  # apartment.py와 동일한 컬렉션 사용

class ExcluusearItem(BaseModel):
    """전용면적 정보"""
    exclusiveArea: str
    tradeCount: int

class ExcluusearResponse(BaseModel):
    """전용면적 검색 응답"""
    result: bool
    resultCount: int
    results: List[ExcluusearItem]
    message: str = None

app = FastAPI()

router = APIRouter()

@router.get('/getexcluusear')
async def GetExcluusear(
    openDate: str = Query(
        None,
        title="개통일",
        description="지하철 개통일을 8자리 숫자로 입력하세요. (입력하지 않으면 이전에 입력한 값이 자동으로 사용)",
        min_length=8,
        max_length=8
    ),
    bubjungdongCode: str = Query(
        None,
        title="법정동코드",
        description="법정동코드 5자리를 입력하세요. (입력하지 않으면 이전에 입력한 값이 자동으로 사용)",
        min_length=5,
        max_length=5
    ),
    apartmentName: str = Query(
        None,
        title="아파트명",
        description="아파트 이름을 입력하세요. (위 apartmentName에 나온 결과 입력)"
    ),

    common_params: CommonParams = Depends(get_common_params)
):
    try:
        # 이전 값 사용 또는 새로운 값 적용
        bubjungdongCode = bubjungdongCode or common_params.bubjungdongCode
        apartmentName = apartmentName or common_params.apartmentName
        
        if not all([bubjungdongCode, apartmentName]):
            return ExcluusearResponse(
                result=False,
                resultCount=0,
                results=[],
                message="법정동코드와 아파트명이 필요합니다."
            )
        
        # 공통 파라미터 업데이트
        update_common_params(
            common_params,
            bubjungdongCode=bubjungdongCode,
            apartmentName=apartmentName
        )
        
        # 개통일 처리
        if openDate:
            # 새로운 개통일이 입력된 경우, MongoDB에 저장
            last_search_col.update_one(
                {"type": "subway_open_date"},
                {"$set": {"date": openDate}},
                upsert=True
            )
        else:
            # 이전 개통일 확인
            last_search = last_search_col.find_one({"type": "subway_open_date"})
            if last_search:
                openDate = last_search.get("date")
            
        if not openDate:
            return ExcluusearResponse(
                result=False,
                resultCount=0,
                results=[],
                message="개통일이 필요합니다."
            )
        
        # 개통일 기준 전후 5년 기간 계산
        open_date = datetime.strptime(openDate, "%Y%m%d")
        start_date = open_date - timedelta(days=5*365)
        end_date = open_date + timedelta(days=5*365)
        
        url = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'
        
        items = []
        areas = []
        
        # 개통일 기준 전후 5년 데이터 조회
        current_date = start_date
        while current_date <= end_date:
            deal_ymd = current_date.strftime("%Y%m")
            
            params = '?serviceKey=' + get_secret("data_apiKey")
            params += '&LAWD_CD=' + bubjungdongCode
            params += '&DEAL_YMD=' + deal_ymd
            params += '&pageNo=1'
            params += '&numOfRows=100'
            
            url_with_params = url + params
            
            try:
                response = requests.get(url_with_params)
                root = ET.fromstring(response.content)
                
                for item in root.findall('.//item'):
                    apt_name = item.find('aptNm').text.strip()
                    
                    # 아파트 이름이 일치하는 경우만 처리
                    if apt_name == apartmentName:
                        area = item.find('excluUseAr').text.strip()
                        if area not in areas:
                            areas.append(area)
                        items.append(item)
                        
            except ET.ParseError as pe:
                print(f"XML 파싱 오류: {str(pe)}")
            except requests.exceptions.RequestException as e:
                print(f"API 요청 실패: {str(e)}")
            
            # 다음 달로 이동
            current_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)
        
        if not areas:
            return ExcluusearResponse(
                result=False,
                resultCount=0,
                results=[],
                message="해당 아파트의 거래 정보가 없습니다."
            )

        # 전용면적별 거래 횟수 계산
        area_counts = {}
        for item in items:
            area = item.find('excluUseAr').text.strip()
            area_counts[area] = area_counts.get(area, 0) + 1

        # 결과 생성
        results = [
            ExcluusearItem(
                exclusiveArea=area,
                tradeCount=area_counts[area]
            ) for area in areas
        ]

        # 거래 횟수 기준으로 정렬
        results.sort(key=lambda x: (-x.tradeCount, float(x.exclusiveArea)))

        return ExcluusearResponse(
            result=True,
            resultCount=len(results),
            results=results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(router)