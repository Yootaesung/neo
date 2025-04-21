import requests
import json
import pandas as pd
from datetime import datetime
import os.path
import xml.etree.ElementTree as ET
from fastapi import FastAPI, Query, APIRouter, Depends
from pydantic import BaseModel
from typing import List

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

class ExcluUseArItem(BaseModel):
    """전용면적 정보"""
    excluUseAr: str
    tradeCount: int

class ExcluUseArResponse(BaseModel):
    """전용면적 검색 응답"""
    result: bool
    resultCount: int
    results: List[ExcluUseArItem]
    message: str = None

app = FastAPI()

router = APIRouter()

from dependencies import get_common_params, update_common_params, CommonParams

@router.get('/getexcluusear')
async def GetExcluUseAr(
    bubjungdongCode: str = Query(
        None,  # 이전 값이 있으면 선택적
        title="법정동코드",
        description="법정동코드 5자리를 입력하세요. 입력하지 않으면 이전에 입력한 값이 자동으로 사용됩니다.",
        min_length=5,
        max_length=5
    ),
    apartmentName: str = Query(
        None,  # 이전 값이 있으면 선택적
        title="아파트명",
        description="아파트 이름을 입력하세요. (위에 apartmentName에서 나온 결과)"
    ),
    common_params: CommonParams = Depends(get_common_params)
):
    # 이전 값 사용 또는 새로운 값 적용
    bubjungdongCode = bubjungdongCode or common_params.bubjungdongCode
    apartmentName = apartmentName or common_params.apartmentName
    
    if not bubjungdongCode or not apartmentName:
        return ExcluUseArResponse(
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
    
    url = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'
    
    # 최근 10년치 데이터를 저장할 리스트
    items = []
    areas = []
    
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
                    apt_nm = item.find('aptNm')
                    exclu_area = item.find('excluUseAr')
                    
                    if apt_nm is not None and exclu_area is not None:
                        if apt_nm.text.strip() == apartmentName:
                            area = exclu_area.text.strip()
                            if area not in areas:
                                areas.append(area)
                            items.append(item)
                                
            except ET.ParseError as pe:
                print(f"XML 파싱 오류: {str(pe)}")
                continue
            except requests.exceptions.RequestException as e:
                print(f"API 요청 실패: {str(e)}")
                continue
    
    if not areas:
        return ExcluUseArResponse(
            result=False,
            resultCount=0,
            results=[]
        )
    
    # 전용면적별로 그룹화하여 빈도수 계산
    area_counts = {}
    for item in items:
        apt_nm = item.find('aptNm')
        exclu_area = item.find('excluUseAr')
        if apt_nm is not None and exclu_area is not None:
            if apt_nm.text.strip() == apartmentName:
                area = exclu_area.text.strip()
                area_counts[area] = area_counts.get(area, 0) + 1

    # 빈도수가 높은 순으로 정렬
    sorted_areas = sorted(
        areas,
        key=lambda x: (-area_counts.get(x, 0), float(x))  # 거래수 내림차순, 면적 오름차순
    )

    print("전용면적별 거래수:")  # 디버깅용
    for area in sorted_areas[:5]:  # 상위 5개만 출력
        print(f"{area}: {area_counts.get(area, 0)}건")

    return ExcluUseArResponse(
        result=True,
        resultCount=len(sorted_areas),
        results=[
            ExcluUseArItem(
                excluUseAr=area,
                tradeCount=area_counts.get(area, 0)  # 거래수도 함께 반환
            ) for area in sorted_areas
        ]
    )

app.include_router(router)