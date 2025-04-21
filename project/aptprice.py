import json
import requests
import os.path
import xml.etree.ElementTree as ET
from fastapi import FastAPI, Query, APIRouter, Depends
from typing import List
from pydantic import BaseModel
from datetime import datetime
from dependencies import get_common_params, update_common_params, CommonParams

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

class PriceItem(BaseModel):
    """거래 가격 정보"""
    dealAmount: str
    dealDate: str  # YYYY-MM-DD 형식
    tradeCount: int

class PriceResponse(BaseModel):
    """거래 가격 검색 응답"""
    result: bool
    resultCount: int
    results: List[PriceItem]

app = FastAPI()

router = APIRouter()

@router.get('/getaptprice')
async def GetAptPrice(
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
        description="아파트 이름을 입력하세요. 입력하지 않으면 이전에 입력한 값이 자동으로 사용됩니다."
    ),
    exclusiveArea: str = Query(
        None,  # 이전 값이 있으면 선택적
        title="전용면적",
        description="전용면적을 입력하세요. 입력하지 않으면 이전에 입력한 값이 자동으로 사용됩니다."
    ),
    floor: str = Query(
        None,  # 이전 값이 있으면 선택적
        title="층",
        description="층수를 입력하세요. (위에 floor에서 나온 결과)"
    ),
    common_params: CommonParams = Depends(get_common_params)
):
    # 이전 값 사용 또는 새로운 값 적용
    bubjungdongCode = bubjungdongCode or common_params.bubjungdongCode
    apartmentName = apartmentName or common_params.apartmentName
    exclusiveArea = exclusiveArea or common_params.exclusiveArea
    floor = floor or common_params.floor
    
    if not all([bubjungdongCode, apartmentName, exclusiveArea, floor]):
        return PriceResponse(
            result=False,
            resultCount=0,
            results=[],
            message="법정동코드, 아파트명, 전용면적, 층수가 필요합니다."
        )
    
    # 공통 파라미터 업데이트
    update_common_params(
        common_params,
        bubjungdongCode=bubjungdongCode,
        apartmentName=apartmentName,
        exclusiveArea=exclusiveArea,
        floor=floor
    )
    
    url = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'
    
    # 최근 10년치 데이터 조회
    current_year = datetime.now().year
    prices = []
    
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

            try:
                response = requests.get(url + params)
                response.raise_for_status()
                
                try:
                    root = ET.fromstring(response.text)
                    items = root.findall('.//item')
                    
                    for item in items:
                        apt_nm = item.find('aptNm')
                        exclu_area = item.find('excluUseAr')
                        item_floor = item.find('floor')
                        deal_amount = item.find('dealAmount')
                        deal_year = item.find('dealYear')
                        deal_month = item.find('dealMonth')
                        deal_day = item.find('dealDay')
                        
                        if all(x is not None for x in [apt_nm, exclu_area, item_floor, 
                                                      deal_amount, deal_year, deal_month, deal_day]):
                            if (apt_nm.text == apartmentName and  # 아파트 이름이 일치하고
                                exclu_area.text.strip() == exclusiveArea and  # 전용면적이 일치하고
                                item_floor.text.strip() == floor):  # 층수가 일치하는 경우
                                
                                # 날짜 형식 변환 (YYYY-MM-DD)
                                date_str = f"{deal_year.text}-{int(deal_month.text):02d}-{int(deal_day.text):02d}"
                                
                                prices.append({
                                    'dealAmount': deal_amount.text.strip(),
                                    'dealDate': date_str
                                })
                    
                except ET.ParseError as pe:
                    return {"오류": f"XML 파싱 오류: {str(pe)}"}
                    
            except requests.exceptions.RequestException as e:
                return {"오류": f"API 요청 실패: {str(e)}"}
    
    if not prices:
        return PriceResponse(
            result=False,
            resultCount=0,
            results=[]
        )
    
    # 가격별로 그룹화하여 빈도수 계산
    price_counts = {}
    for price in prices:
        amount = price['dealAmount']
        price_counts[amount] = price_counts.get(amount, 0) + 1

    # 빈도수가 높은 순으로 정렬, 같은 빈도수면 가격이 높은 순
    prices.sort(key=lambda x: (
        -price_counts.get(x['dealAmount'], 0),  # 거래수 내림차순
        -int(x['dealAmount'].replace(',', '')),  # 가격 내림차순
        x['dealDate']  # 날짜 오름차순
    ))

    print("가격별 거래수:")  # 디버깅용
    seen_prices = set()
    for price in prices:
        if price['dealAmount'] not in seen_prices:
            seen_prices.add(price['dealAmount'])
            if len(seen_prices) > 5:  # 상위 5개만 출력
                break
            print(f"{price['dealAmount']}만원: {price_counts.get(price['dealAmount'], 0)}건")

    return PriceResponse(
        result=True,
        resultCount=len(prices),
        results=[
            PriceItem(
                dealAmount=price['dealAmount'],
                dealDate=price['dealDate'],
                tradeCount=price_counts.get(price['dealAmount'], 0)  # 거래수도 함께 반환
            ) for price in prices
        ]
    )

app.include_router(router)
