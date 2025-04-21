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

class FloorItem(BaseModel):
    """층수 정보"""
    floor: str
    tradeCount: int

class FloorResponse(BaseModel):
    """층수 검색 응답"""
    result: bool
    resultCount: int
    results: List[FloorItem]
    message: str = None

app = FastAPI()

router = APIRouter()

@router.get('/getfloor')
async def GetFloor(
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
    common_params: CommonParams = Depends(get_common_params)
):
    # 이전 값 사용 또는 새로운 값 적용
    bubjungdongCode = bubjungdongCode or common_params.bubjungdongCode
    apartmentName = apartmentName or common_params.apartmentName
    exclusiveArea = exclusiveArea or common_params.exclusiveArea
    
    if not all([bubjungdongCode, apartmentName, exclusiveArea]):
        return FloorResponse(
            result=False,
            resultCount=0,
            results=[],
            message="법정동코드, 아파트명, 전용면적이 필요합니다."
        )
    
    # 공통 파라미터 업데이트
    update_common_params(
        common_params,
        bubjungdongCode=bubjungdongCode,
        apartmentName=apartmentName,
        exclusiveArea=exclusiveArea
    )
    
    url = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'
    
    # 최근 10년치 데이터를 저장할 리스트
    items = []
    floors = []
    
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
                    floor_num = item.find('floor')
                    
                    if apt_nm is not None and exclu_area is not None and floor_num is not None:
                        if (apt_nm.text.strip() == apartmentName and 
                            exclu_area.text.strip() == exclusiveArea):
                            floor = floor_num.text.strip()
                            if floor not in floors:
                                floors.append(floor)
                            items.append(item)
                                
            except ET.ParseError as pe:
                print(f"XML 파싱 오류: {str(pe)}")
                continue
            except requests.exceptions.RequestException as e:
                print(f"API 요청 실패: {str(e)}")
                continue
    
    if not floors:
        return FloorResponse(
            result=False,
            resultCount=0,
            results=[]
        )
    
    # 층수별로 그룹화하여 빈도수 계산
    floor_counts = {}
    for item in items:
        apt_nm = item.find('aptNm')
        exclu_area = item.find('excluUseAr')
        floor_num = item.find('floor')
        if apt_nm is not None and exclu_area is not None and floor_num is not None:
            if (apt_nm.text.strip() == apartmentName and 
                exclu_area.text.strip() == exclusiveArea):
                floor = floor_num.text.strip()
                floor_counts[floor] = floor_counts.get(floor, 0) + 1

    # 빈도수가 높은 순으로 정렬
    sorted_floors = sorted(
        floors,
        key=lambda x: (-floor_counts.get(x, 0), int(x))  # 거래수 내림차순, 층수 오름차순
    )

    print("층수별 거래수:")  # 디버깅용
    for floor in sorted_floors[:5]:  # 상위 5개만 출력
        print(f"{floor}층: {floor_counts.get(floor, 0)}건")

    return FloorResponse(
        result=True,
        resultCount=len(sorted_floors),
        results=[
            FloorItem(
                floor=floor,
                tradeCount=floor_counts.get(floor, 0)  # 거래수도 함께 반환
            ) for floor in sorted_floors
        ]
    )

app.include_router(router)