import requests
import json
import pandas as pd
from datetime import datetime
import os.path
import xml.etree.ElementTree as ET
from fastapi import FastAPI, Query, APIRouter, Depends
from typing import List
from pydantic import BaseModel
from dependencies import get_common_params, update_common_params, CommonParams

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

class ApartmentItem(BaseModel):
    """아파트 정보"""
    apartmentName: str
    tradeCount: int

class ApartmentResponse(BaseModel):
    """아파트 검색 응답"""
    result: bool
    resultCount: int
    results: List[ApartmentItem]

router = APIRouter()

@router.get('/getapartmentdata')
async def GetApartmentData(
    bubjungdongCode: str = Query(
        None,  
        title="법정동코드",
        description="법정동코드 5자리를 입력하세요. 입력하지 않으면 이전에 입력한 값이 자동으로 사용됩니다.",
        min_length=5,
        max_length=5
    ),
    common_params: CommonParams = Depends(get_common_params)
):
    # 공통 파라미터 업데이트
    update_common_params(common_params, bubjungdongCode=bubjungdongCode)
    
    url = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'
    
    # 최근 10년치 데이터를 저장할 리스트
    items = []
    apartment_names = []
    
    # 현재 년월 구하기
    current_year = datetime.now().year
    
    # 각 연도별로 1월부터 12월까지 조회
    for year in range(current_year - 10, current_year + 1):
        for month in range(1, 13):
            # 현재 월 이후의 데이터는 조회하지 않음
            if year == current_year and month > datetime.now().month:
                break
                
            deal_ymd = f"{year}{month:02d}"
            
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
                continue
            except requests.exceptions.RequestException as e:
                print(f"API 요청 실패: {str(e)}")
                continue
    
    if not apartment_names:
        return ApartmentResponse(
            result=False,
            resultCount=0,
            results=[]
        )
    
    # 아파트 이름별로 그룹화하여 빈도수 계산
    apartment_counts = {}
    for item in items:
        apt_nm = item.find('aptNm')
        if apt_nm is not None:
            name = apt_nm.text.strip()
            apartment_counts[name] = apartment_counts.get(name, 0) + 1

    # 빈도수가 높은 순으로 정렬
    sorted_apartment_names = sorted(
        apartment_names,
        key=lambda x: (-apartment_counts.get(x, 0), x)  # 거래수 내림차순, 이름 오름차순
    )

    print("아파트별 거래수:")  # 디버깅용
    for name in sorted_apartment_names[:5]:  # 상위 5개만 출력
        print(f"{name}: {apartment_counts.get(name, 0)}건")

    return ApartmentResponse(
        result=True,
        resultCount=len(sorted_apartment_names),
        results=[
            ApartmentItem(
                apartmentName=name,
                tradeCount=apartment_counts.get(name, 0)  # 거래수도 함께 반환
            ) for name in sorted_apartment_names
        ]
    )

app.include_router(router)