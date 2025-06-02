import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import os.path
import xml.etree.ElementTree as ET
from fastapi import FastAPI, Query, APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from dependencies import get_common_params, update_common_params, CommonParams
from database import client

BASE_DIR = os.path.dirname(os.path.abspath(os.path.relpath("./")))
secret_file = os.path.join(BASE_DIR, 'secret.json')

with open(secret_file) as f:
    secrets = json.loads(f.read())

def get_secret(setting, secrets=secrets):
    try:
        return secrets[setting]
    except KeyError:
        errorMsg = "Set the {} environment variable.".format(setting)
        return errorMsg

app = FastAPI()

# MongoDB 연결
mydb = client["apartment"]
last_search_col = mydb["last_search"]  # 마지막 검색어 저장용 컬렉션

class ApartmentItem(BaseModel):
    """아파트 정보"""
    apartmentName: str
    tradeCount: int

class ApartmentResponse(BaseModel):
    """아파트 검색 응답"""
    result: bool
    resultCount: int
    results: List[ApartmentItem]
    message: str = None

router = APIRouter()

@router.get('/getapartment')
async def GetApartment(
    openDate: str = Query(
        None,
        title="개통일",
        description="지하철 개통일을 8자리 숫자로 입력하세요. (위 subway에 나온 결과 입력)",
        min_length=8,
        max_length=8
    ),
    bubjungdongCode: str = Query(
        None,
        title="법정동코드",
        description="법정동코드 5자리를 입력하세요. (위 bubjungdongCode에 나온 결과 입력)",
        min_length=5,
        max_length=5
    ),
    common_params: CommonParams = Depends(get_common_params)
):
    try:
        # 이전 값 사용 또는 새로운 값 적용
        bubjungdongCode = bubjungdongCode or common_params.bubjungdongCode
        
        if not bubjungdongCode:
            return ApartmentResponse(
                result=False,
                resultCount=0,
                results=[],
                message="법정동코드가 필요합니다."
            )
        
        # 공통 파라미터 업데이트
        update_common_params(
            common_params,
            bubjungdongCode=bubjungdongCode
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
            return ApartmentResponse(
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
        apartment_names = []
        
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
                    items.append(item)
                    apartment_name = item.find('aptNm').text.strip()
                    if apartment_name not in apartment_names:
                        apartment_names.append(apartment_name)
                        
            except ET.ParseError as pe:
                print(f"XML 파싱 오류: {str(pe)}")
            except requests.exceptions.RequestException as e:
                print(f"API 요청 실패: {str(e)}")
            
            # 다음 달로 이동
            current_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)
    
        if not apartment_names:
            return ApartmentResponse(
                result=False,
                resultCount=0,
                results=[]
            )

        # 아파트별 거래 횟수 계산
        trade_counts = {}
        for item in items:
            apartment_name = item.find('aptNm').text.strip()
            trade_counts[apartment_name] = trade_counts.get(apartment_name, 0) + 1

        # 결과 생성
        results = [
            ApartmentItem(
                apartmentName=name,
                tradeCount=trade_counts[name]
            ) for name in apartment_names
        ]

        # 거래 횟수 기준으로 정렬
        results.sort(key=lambda x: x.tradeCount, reverse=True)

        return ApartmentResponse(
            result=True,
            resultCount=len(results),
            results=results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(router)