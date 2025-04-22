import json
import requests
import os.path
import xml.etree.ElementTree as ET
from fastapi import FastAPI, Query, APIRouter, Depends, HTTPException, Response
from typing import List
from pydantic import BaseModel
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from dependencies import get_common_params, update_common_params, CommonParams
from database import client
from fastapi.responses import FileResponse, JSONResponse
import matplotlib.font_manager as fm
import matplotlib.ticker as ticker
from uuid import uuid4
from fastapi.staticfiles import StaticFiles

# 폰트 설정
plt.rcParams['font.family'] = 'NanumBarunGothic'
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

PRICE_UNIT = 10000000  # 천만원 단위

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # neo 디렉토리
PROJECT_DIR = os.path.join(BASE_DIR, 'project')  # project 디렉토리
STATIC_DIR = os.path.join(PROJECT_DIR, 'static')
IMAGE_DIR = os.path.join(STATIC_DIR, 'images')

# 디렉토리가 없으면 생성
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)

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
    saleDay: str
    price: int

class AptPriceResponse(BaseModel):
    """아파트 가격 검색 응답"""
    result: bool
    resultCount: int
    results: List[AptPriceItem]
    message: str = None

class LineGraphResponse(BaseModel):
    """선 그래프 응답"""
    result: bool
    message: str = None
    image_url: str = None

class BarChartResponse(BaseModel):
    """막대 그래프 응답"""
    result: bool
    message: str = None
    image_url: str = None

app = FastAPI()

# 정적 파일 서비스 설정
IMAGE_DIR = os.path.join(STATIC_DIR, 'images')
os.makedirs(IMAGE_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

router = APIRouter()

@router.get('/getaptprice')
async def GetAptPrice(
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
        description="아파트 이름을 입력하세요. (입력하지 않으면 이전에 입력한 값이 자동으로 사용)"
    ),
    exclusiveArea: str = Query(
        None,
        title="전용면적",
        description="전용면적을 입력하세요. (입력하지 않으면 이전에 입력한 값이 자동으로 사용)"
    ),
    floor: str = Query(
        None,
        title="층",
        description="층을 입력하세요. (위 floor에 나온 결과 입력)"
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
            last_open_date = last_search_col.find_one({"type": "subway_open_date"})
            if last_open_date:
                openDate = last_open_date["date"]

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
                response = requests.get(url_with_params, timeout=10)  # timeout 추가
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
                    price_elem = item.find('dealAmount')
                    year_elem = item.find('dealYear')
                    month_elem = item.find('dealMonth')
                    day_elem = item.find('dealDay')
                    
                    # 모든 필요한 요소가 존재하는지 확인
                    if all([
                        apt_name_elem is not None and apt_name_elem.text,
                        area_elem is not None and area_elem.text,
                        floor_elem is not None and floor_elem.text,
                        price_elem is not None and price_elem.text,
                        year_elem is not None and year_elem.text,
                        month_elem is not None and month_elem.text,
                        day_elem is not None and day_elem.text
                    ]):
                        apt_name = apt_name_elem.text.strip()
                        area = area_elem.text.strip()
                        item_floor = floor_elem.text.strip()
                        
                        # 아파트 이름, 전용면적, 층이 일치하는 경우만 처리
                        if (apt_name == apartmentName and 
                            area == exclusiveArea and 
                            item_floor == floor):
                            
                            # 날짜 형식 변환 (YYYY-MM-DD)
                            year = year_elem.text.strip()
                            month = month_elem.text.strip()
                            day = day_elem.text.strip()
                            
                            sale_date = f"{year}-{int(month):02d}-{int(day):02d}"
                            
                            # 가격 변환 (만원 -> 원)
                            price = int(price_elem.text.strip().replace(',', '')) * 10000
                            
                            results.append(AptPriceItem(
                                saleDay=sale_date,
                                price=price
                            ))
                        
            except ET.ParseError as pe:
                print(f"XML 파싱 오류: {str(pe)}")
            except (ValueError, AttributeError) as e:
                print(f"데이터 처리 오류: {str(e)}")
            except requests.exceptions.RequestException as e:
                print(f"API 요청 실패: {str(e)}")
            except Exception as e:  # 더 구체적인 예외 처리 추가
                print(f"기타 오류: {str(e)}")
                if not isinstance(e, (ET.ParseError, ValueError, AttributeError, requests.exceptions.RequestException)):
                    raise
            except Exception as e:
                print(f"Error: {str(e)}")
            
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
        results.sort(key=lambda x: x.saleDay, reverse=True)

        return AptPriceResponse(
            result=True,
            resultCount=len(results),
            results=results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/getaptpricelinegraph')
async def get_line_graph(
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
        description="아파트 이름을 입력하세요. (입력하지 않으면 이전에 입력한 값이 자동으로 사용)"
    ),
    exclusiveArea: str = Query(
        None,
        title="전용면적",
        description="전용면적을 입력하세요. (입력하지 않으면 이전에 입력한 값이 자동으로 사용)"
    ),
    floor: str = Query(
        None,
        title="층",
        description="층을 입력하세요. (입력하지 않으면 이전에 입력한 값이 자동으로 사용)"
    ),
    common_params: CommonParams = Depends(get_common_params)
):
    try:
        # static 디렉토리 생성
        os.makedirs(STATIC_DIR, exist_ok=True)
        
        # 이전 값 사용 또는 새로운 값 적용
        bubjungdongCode = bubjungdongCode or common_params.bubjungdongCode
        apartmentName = apartmentName or common_params.apartmentName
        exclusiveArea = exclusiveArea or common_params.exclusiveArea
        floor = floor or common_params.floor

        # 개통일 처리
        if openDate:
            # 새로운 개통일이 입력된 경우, MongoDB에 저장
            last_search_col.update_one(
                {"type": "subway_open_date"},
                {"$set": {"date": openDate}},
                upsert=True
            )
        else:
            # 이전 개통일 가져오기
            last_open_date = last_search_col.find_one({"type": "subway_open_date"})
            if last_open_date:
                openDate = last_open_date["date"]

        # 필수 파라미터 체크
        if not all([openDate, bubjungdongCode, apartmentName, exclusiveArea]):
            return LineGraphResponse(
                result=False,
                message="개통일, 법정동코드, 아파트명, 전용면적을 모두 입력해주세요."
            )

        # 파라미터 업데이트
        update_common_params(common_params, 
            openDate=openDate,
            bubjungdongCode=bubjungdongCode,
            apartmentName=apartmentName,
            exclusiveArea=exclusiveArea,
            floor=floor
        )
        
        # 개통일 기준 전후 5년 기간 계산
        open_date = datetime.strptime(openDate, "%Y%m%d")
        start_date = open_date - timedelta(days=5*365)
        end_date = open_date + timedelta(days=5*365)

        url = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'
        dates = []
        prices = []

        # 데이터 수집
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
                response = requests.get(url_with_params, timeout=10)  # timeout 추가
                root = ET.fromstring(response.content)
                
                for item in root.findall('.//item'):
                    apt_name = item.find('aptNm').text.strip()
                    area = item.find('excluUseAr').text.strip()
                    item_floor = item.find('floor').text.strip()
                    
                    if (apt_name == apartmentName and 
                        area == exclusiveArea and 
                        item_floor == floor):
                        
                        year = item.find('dealYear').text.strip()
                        month = item.find('dealMonth').text.strip()
                        price = int(item.find('dealAmount').text.strip().replace(',', '')) * 10000
                        
                        deal_date = datetime.strptime(f"{year}{month:0>2}", "%Y%m")
                        dates.append(deal_date)
                        prices.append(price)
                        
            except ET.ParseError as pe:
                print(f"XML 파싱 오류: {str(pe)}")
            except (ValueError, AttributeError) as e:
                print(f"데이터 처리 오류: {str(e)}")
            except requests.exceptions.RequestException as e:
                print(f"API 요청 실패: {str(e)}")
            except Exception as e:  # 더 구체적인 예외 처리 추가
                print(f"기타 오류: {str(e)}")
                if not isinstance(e, (ET.ParseError, ValueError, AttributeError, requests.exceptions.RequestException)):
                    raise
            except Exception as e:
                print(f"Error: {str(e)}")
            
            current_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)

        if not dates:
            return LineGraphResponse(
                result=False,
                message="거래 데이터가 없습니다."
            )

        # 데이터 정렬
        sorted_data = sorted(zip(dates, prices))
        dates, prices = zip(*sorted_data)

        # 빈 데이터 채우기
        filled_dates = []
        filled_prices = []
        
        for i in range(len(dates)-1):
            filled_dates.append(dates[i])
            filled_prices.append(prices[i])
            
            months_diff = (dates[i+1].year - dates[i].year) * 12 + dates[i+1].month - dates[i].month
            if months_diff > 1:
                price_diff = prices[i+1] - prices[i]
                monthly_increment = price_diff / months_diff
                
                for j in range(1, months_diff):
                    interpolated_date = dates[i] + timedelta(days=30.44 * j)  # 평균 한 달
                    interpolated_price = prices[i] + (monthly_increment * j)
                    
                    filled_dates.append(interpolated_date)
                    filled_prices.append(interpolated_price)
        
        filled_dates.append(dates[-1])
        filled_prices.append(prices[-1])

        # 그래프 생성
        plt.figure(figsize=(12, 6))
        # 가격을 천만원 단위로 변환
        filled_prices = [p / PRICE_UNIT for p in filled_prices]
        plt.plot(filled_dates, filled_prices, color='blue', linewidth=2)
        
        # 개통일 표시
        plt.axvline(x=open_date, color='r', linestyle='--', label='개통일')
        
        # x축 설정
        plt.gca().xaxis.set_major_locator(mdates.YearLocator())
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        plt.gca().xaxis.set_minor_locator(mdates.MonthLocator())
        
        # 격자 설정
        plt.grid(True, which='major', linestyle='-', alpha=0.5)  # 년도 격자선
        plt.grid(True, which='minor', linestyle=':', alpha=0.3)  # 월 격자선
        plt.grid(True, axis='y', alpha=0.3)  # y축 격자선
        
        # Y축 포맷 설정 (천만원 단위)
        plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{x:.1f}'))
        
        plt.title(f'{apartmentName}({exclusiveArea}㎡) {floor}층 실거래가 추이')
        plt.xlabel('날짜')
        plt.ylabel('실거래가 (단위: 천만원)')
        
        plt.legend()
        
        # 이미지 파일 저장
        image_filename = f"line_graph_{uuid4()}.png"
        image_path = os.path.join(IMAGE_DIR, image_filename)
        plt.savefig(image_path, bbox_inches='tight', dpi=300)
        plt.close()
            
        # 이미지 URL 생성
        image_url = f"/static/images/{image_filename}"
        return LineGraphResponse(result=True, image_url=image_url)

    except Exception as e:
        print(f"Error in get_line_graph: {str(e)}")  # 에러 로깅 추가
        return LineGraphResponse(
            result=False,
            message=str(e)
        )

@router.get('/getaptpricebarchart')  # 엔드포인트 이름 변경
async def get_bar_chart(
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
        description="아파트 이름을 입력하세요. (입력하지 않으면 이전에 입력한 값이 자동으로 사용)"
    ),
    exclusiveArea: str = Query(
        None,
        title="전용면적",
        description="전용면적을 입력하세요. (입력하지 않으면 이전에 입력한 값이 자동으로 사용)"
    ),
    floor: str = Query(
        None,
        title="층",
        description="층을 입력하세요. (입력하지 않으면 이전에 입력한 값이 자동으로 사용)"
    ),
    common_params: CommonParams = Depends(get_common_params)
):
    try:
        # static 디렉토리 생성
        os.makedirs(STATIC_DIR, exist_ok=True)
        
        # 이전 값 사용 또는 새로운 값 적용
        bubjungdongCode = bubjungdongCode or common_params.bubjungdongCode
        apartmentName = apartmentName or common_params.apartmentName
        exclusiveArea = exclusiveArea or common_params.exclusiveArea
        floor = floor or common_params.floor

        # 개통일 처리
        if openDate:
            # 새로운 개통일이 입력된 경우, MongoDB에 저장
            last_search_col.update_one(
                {"type": "subway_open_date"},
                {"$set": {"date": openDate}},
                upsert=True
            )
        else:
            # 이전 개통일 가져오기
            last_open_date = last_search_col.find_one({"type": "subway_open_date"})
            if last_open_date:
                openDate = last_open_date["date"]

        # 필수 파라미터 체크
        if not all([openDate, bubjungdongCode, apartmentName, exclusiveArea]):
            return BarChartResponse(
                result=False,
                message="개통일, 법정동코드, 아파트명, 전용면적을 모두 입력해주세요."
            )

        # 파라미터 업데이트
        update_common_params(common_params, 
            openDate=openDate,
            bubjungdongCode=bubjungdongCode,
            apartmentName=apartmentName,
            exclusiveArea=exclusiveArea,
            floor=floor
        )
        
        # 개통일 기준 전후 5년 기간 계산
        open_date = datetime.strptime(openDate, "%Y%m%d")
        start_date = open_date - timedelta(days=5*365)
        end_date = open_date + timedelta(days=5*365)

        url = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'
        before_prices = []
        after_prices = []

        # 데이터 수집
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
                response = requests.get(url_with_params, timeout=10)  # timeout 추가
                root = ET.fromstring(response.content)
                
                for item in root.findall('.//item'):
                    apt_name = item.find('aptNm').text.strip()
                    area = item.find('excluUseAr').text.strip()
                    item_floor = item.find('floor').text.strip()
                    
                    if (apt_name == apartmentName and 
                        area == exclusiveArea and 
                        item_floor == floor):
                        
                        year = item.find('dealYear').text.strip()
                        month = item.find('dealMonth').text.strip()
                        price = int(item.find('dealAmount').text.strip().replace(',', '')) * 10000
                        
                        deal_date = datetime.strptime(f"{year}{month:0>2}", "%Y%m")
                        
                        if deal_date < open_date:
                            before_prices.append(price)
                        else:
                            after_prices.append(price)
                        
            except ET.ParseError as pe:
                print(f"XML 파싱 오류: {str(pe)}")
            except (ValueError, AttributeError) as e:
                print(f"데이터 처리 오류: {str(e)}")
            except requests.exceptions.RequestException as e:
                print(f"API 요청 실패: {str(e)}")
            except Exception as e:  # 더 구체적인 예외 처리 추가
                print(f"기타 오류: {str(e)}")
                if not isinstance(e, (ET.ParseError, ValueError, AttributeError, requests.exceptions.RequestException)):
                    raise
            except Exception as e:
                print(f"Error: {str(e)}")
            
            current_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)

        if not before_prices and not after_prices:
            return BarChartResponse(
                result=False,
                message="거래 데이터가 없습니다."
            )

        # 평균 계산
        before_mean = np.mean(before_prices) if before_prices else 0
        after_mean = np.mean(after_prices) if after_prices else 0
        
        # 증감률 계산
        change_percent = ((after_mean - before_mean) / before_mean * 100) if before_mean > 0 else 0

        # 그래프 생성
        plt.figure(figsize=(10, 6))
        
        # 천만원 단위로 변환
        before_mean_adj = before_mean / PRICE_UNIT
        after_mean_adj = after_mean / PRICE_UNIT
        
        # 막대 그래프 생성 (바 간격 좁힘)
        bars = plt.bar([0, 0.6], [before_mean_adj, after_mean_adj], 
                      color=['blue', 'red'], width=0.3)
        
        # 축 설정
        plt.xticks([0, 0.6], ['개통 전', '개통 후'])
        plt.ylabel('실거래가 (단위: 천만원)')
        
        # 막대 위에 값 표시 (천만원 단위, 소수점 1자리)
        ymin, ymax = plt.ylim()
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, height + (ymax-ymin)*0.02,  # 바 위에 위치
                    f'{height:.1f}',
                    ha='center', va='bottom', fontweight='bold', color='black')
        
        # 화살표 추가 (개통 전 -> 개통 후)
        arrow_start = (bars[0].get_x() + bars[0].get_width()/2, before_mean_adj)
        arrow_end = (bars[1].get_x() + bars[1].get_width()/2, after_mean_adj)
        
        # 화살표의 곡률 계산
        rad = 0.2
        # 화살표 중간점의 실제 y 위치 계산 (곡선 고려)
        curve_height = abs(arrow_end[0] - arrow_start[0]) * rad
        if after_mean_adj > before_mean_adj:
            mid_y = (arrow_start[1] + arrow_end[1]) / 2 + curve_height
        else:
            mid_y = (arrow_start[1] + arrow_end[1]) / 2 - curve_height
        
        # 화살표 추가
        plt.annotate(
            '',  # 화살표만 그리기
            xy=arrow_end,
            xytext=arrow_start,
            arrowprops=dict(
                arrowstyle='->',
                color='purple',
                lw=2,
                connectionstyle=f'arc3,rad={rad}'
            )
        )
        
        # 증감률 텍스트 추가 (화살표 곡선 위에 바로 배치)
        text_offset = (ymax-ymin)*0.03  # 작은 오프셋
        va_position = 'bottom' if after_mean_adj > before_mean_adj else 'top'
        text_y = mid_y + text_offset if va_position == 'bottom' else mid_y - text_offset
        
        plt.text((arrow_start[0] + arrow_end[0]) / 2, text_y,
                f'{change_percent:+.1f}%',
                ha='center',
                va=va_position,
                fontweight='bold',
                color='black')
        
        plt.title(f'{apartmentName}({exclusiveArea}㎡) {floor}층 개통 전후 5년간 실거래가 평균')
        
        # y축 범위 조정
        ymin = min(before_mean_adj, after_mean_adj) * 0.8
        ymax = max(before_mean_adj, after_mean_adj) * 1.2
        plt.ylim(ymin, ymax)
        
        # 이미지 파일 저장
        image_filename = f"bar_chart_{uuid4()}.png"
        image_path = os.path.join(IMAGE_DIR, image_filename)
        plt.savefig(image_path, bbox_inches='tight', dpi=300)
        plt.close()
            
        # 이미지 URL 생성
        image_url = f"/static/images/{image_filename}"
        return BarChartResponse(result=True, image_url=image_url)

    except Exception as e:
        print(f"Error in get_bar_chart: {str(e)}")  # 에러 로깅 추가
        return BarChartResponse(
            result=False,
            message=str(e)
        )

app.include_router(router)
