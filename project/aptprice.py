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

class AptPriceItem(BaseModel):
    """아파트 가격 정보"""
    dealYear: str
    dealMonth: str
    price: int
    floor: str
    exclusiveArea: str

class AptPriceResponse(BaseModel):
    """아파트 가격 검색 응답"""
    result: bool
    resultCount: int
    results: List[AptPriceItem]
    message: str = None

app = FastAPI()

router = APIRouter()

@router.get('/getaptprice')
async def GetAptPrice(
    bubjungdongCode: str = Query(
        None,
        title="법정동코드",
        description="법정동코드 5자리를 입력하세요. 입력하지 않으면 이전에 입력한 값이 자동으로 사용됩니다.",
        min_length=5,
        max_length=5
    ),
    apartmentName: str = Query(
        None,
        title="아파트명",
        description="아파트 이름을 입력하세요. 입력하지 않으면 이전에 입력한 값이 자동으로 사용됩니다."
    ),
    exclusiveArea: str = Query(
        None,
        title="전용면적",
        description="전용면적을 입력하세요. 입력하지 않으면 이전에 입력한 값이 자동으로 사용됩니다."
    ),
    floor: str = Query(
        None,
        title="층",
        description="층을 입력하세요. 입력하지 않으면 이전에 입력한 값이 자동으로 사용됩니다."
    ),
    openDate: str = Query(
        None,
        title="개통일",
        description="지하철 개통일을 8자리 숫자로 입력하세요. 입력하지 않으면 이전에 입력한 값이 자동으로 사용됩니다.",
        min_length=8,
        max_length=8
    ),
    common_params: CommonParams = Depends(get_common_params)
):
    try:
        # 이전 값 사용 또는 새로운 값 적용
        bubjungdongCode = bubjungdongCode or common_params.bubjungdongCode
        apartmentName = apartmentName or common_params.apartmentName
        exclusiveArea = exclusiveArea or common_params.exclusiveArea
        floor = floor or common_params.floor
        
        if not all([bubjungdongCode, apartmentName, exclusiveArea, floor]):
            return AptPriceResponse(
                result=False,
                resultCount=0,
                results=[],
                message="법정동코드, 아파트명, 전용면적, 층이 필요합니다."
            )
        
        # 공통 파라미터 업데이트
        update_common_params(
            common_params,
            bubjungdongCode=bubjungdongCode,
            apartmentName=apartmentName,
            exclusiveArea=exclusiveArea,
            floor=floor
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
            return AptPriceResponse(
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
        
        results = []
        
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
                
                # 디버깅을 위해 첫 번째 item의 모든 필드를 출력
                first_item = root.find('.//item')
                if first_item is not None:
                    print("=== XML 필드 디버깅 ===")
                    for child in first_item:
                        print(f"{child.tag}: {child.text}")
                    print("=====================")
                
                for item in root.findall('.//item'):
                    # None 체크를 포함하여 안전하게 데이터 추출
                    apt_name_elem = item.find('aptNm')
                    area_elem = item.find('excluUseAr')
                    floor_elem = item.find('floor')
                    price_elem = item.find('거래금액')
                    year_elem = item.find('년')
                    month_elem = item.find('월')
                    
                    # 모든 필요한 요소가 존재하는지 확인
                    if all([
                        apt_name_elem is not None and apt_name_elem.text,
                        area_elem is not None and area_elem.text,
                        floor_elem is not None and floor_elem.text,
                        price_elem is not None and price_elem.text,
                        year_elem is not None and year_elem.text,
                        month_elem is not None and month_elem.text
                    ]):
                        apt_name = apt_name_elem.text.strip()
                        area = area_elem.text.strip()
                        item_floor = floor_elem.text.strip()
                        
                        # 아파트 이름, 전용면적, 층이 일치하는 경우만 처리
                        if (apt_name == apartmentName and 
                            area == exclusiveArea and 
                            item_floor == floor):
                            
                            # 거래 금액에서 쉼표 제거하고 정수로 변환
                            price = int(price_elem.text.strip().replace(',', '')) * 10000  # 만원 단위를 원 단위로 변환
                            
                            results.append(AptPriceItem(
                                dealYear=year_elem.text.strip(),
                                dealMonth=month_elem.text.strip(),
                                price=price,
                                floor=floor_elem.text.strip(),
                                exclusiveArea=area_elem.text.strip()
                            ))
                        
            except ET.ParseError as pe:
                print(f"XML 파싱 오류: {str(pe)}")
            except (ValueError, AttributeError) as e:
                print(f"데이터 처리 오류: {str(e)}")
            except requests.exceptions.RequestException as e:
                print(f"API 요청 실패: {str(e)}")
            
            # 다음 달로 이동
            current_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)
        
        if not results:
            return AptPriceResponse(
                result=False,
                resultCount=0,
                results=[],
                message="해당 조건의 거래 정보가 없습니다."
            )

        # 결과 생성
        # 거래일 기준으로 정렬 (최신순)
        results.sort(key=lambda x: (int(x.dealYear), int(x.dealMonth)), reverse=True)

        return AptPriceResponse(
            result=True,
            resultCount=len(results),
            results=results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(router)
