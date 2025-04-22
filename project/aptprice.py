import json
import requests
import os.path
import xml.etree.ElementTree as ET
from fastapi import FastAPI, Query, APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
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

class LineGraphResponse(BaseModel):
    """선 그래프 응답"""
    result: bool
    imageUrl: str = None
    message: str = None

class BarChartResponse(BaseModel):
    """막대 그래프 응답"""
    result: bool
    imageUrl: str = None
    beforeAvg: float = None
    afterAvg: float = None
    changePercent: float = None
    message: str = None

app = FastAPI()

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
                    price_elem = item.find('dealAmount')
                    year_elem = item.find('dealYear')
                    month_elem = item.find('dealMonth')
                    
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
        # API 호출을 위한 파라미터 설정
        bubjungdongCode = bubjungdongCode or common_params.bubjungdongCode
        apartmentName = apartmentName or common_params.apartmentName
        exclusiveArea = exclusiveArea or common_params.exclusiveArea
        floor = floor or common_params.floor
        openDate = openDate or common_params.openDate

        if not all([openDate, bubjungdongCode, apartmentName, exclusiveArea, floor]):
            return LineGraphResponse(
                result=False,
                message="모든 파라미터가 필요합니다."
            )

        # 공통 파라미터 업데이트
        update_common_params(
            common_params,
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
                response = requests.get(url_with_params)
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
        plt.plot(filled_dates, filled_prices, '-o', markersize=4)
        
        # 개통일 표시
        plt.axvline(x=open_date, color='red', linestyle='--', label='개통일')
        
        # x축 설정
        plt.gca().xaxis.set_major_locator(mdates.YearLocator())
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        
        # 월별 눈금 추가 (시계 모양)
        plt.gca().xaxis.set_minor_locator(mdates.MonthLocator())
        plt.grid(True, which='minor', linestyle=':')
        
        plt.title(f'{apartmentName} {floor}층 거래가격 추이')
        plt.xlabel('년도')
        plt.ylabel('거래금액 (원)')
        plt.legend()
        
        # 그래프 저장
        graph_path = os.path.join(BASE_DIR, 'static', 'linegraph.png')
        os.makedirs(os.path.dirname(graph_path), exist_ok=True)
        plt.savefig(graph_path)
        plt.close()

        return LineGraphResponse(
            result=True,
            imageUrl="/static/linegraph.png"
        )

    except Exception as e:
        return LineGraphResponse(
            result=False,
            message=str(e)
        )

@router.get('/getaptpricebarchart')
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
        # API 호출을 위한 파라미터 설정
        bubjungdongCode = bubjungdongCode or common_params.bubjungdongCode
        apartmentName = apartmentName or common_params.apartmentName
        exclusiveArea = exclusiveArea or common_params.exclusiveArea
        floor = floor or common_params.floor
        openDate = openDate or common_params.openDate

        if not all([openDate, bubjungdongCode, apartmentName, exclusiveArea, floor]):
            return BarChartResponse(
                result=False,
                message="모든 파라미터가 필요합니다."
            )

        # 공통 파라미터 업데이트
        update_common_params(
            common_params,
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
                response = requests.get(url_with_params)
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
                        
            except Exception as e:
                print(f"Error: {str(e)}")
            
            current_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)

        if not before_prices and not after_prices:
            return BarChartResponse(
                result=False,
                message="거래 데이터가 없습니다."
            )

        # 평균 계산
        before_avg = np.mean(before_prices) if before_prices else 0
        after_avg = np.mean(after_prices) if after_prices else 0
        
        # 증감률 계산
        change_percent = ((after_avg - before_avg) / before_avg * 100) if before_avg > 0 else 0

        # 그래프 생성
        plt.figure(figsize=(8, 6))
        
        # 막대 그래프
        x = ['Before', 'After']
        heights = [before_avg, after_avg]
        bars = plt.bar(x, heights)
        
        # 막대 위에 값 표시
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:,.0f}원',
                    ha='center', va='bottom')
        
        # 증감률 표시
        plt.title(f'{apartmentName} {floor}층 평균 거래가격 비교\n(증감률: {change_percent:.1f}%)')
        plt.ylabel('거래금액 (원)')
        
        # y축 단위 조정
        plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
        
        # 그래프 저장
        graph_path = os.path.join(BASE_DIR, 'static', 'barchart.png')
        os.makedirs(os.path.dirname(graph_path), exist_ok=True)
        plt.savefig(graph_path)
        plt.close()

        return BarChartResponse(
            result=True,
            imageUrl="/static/barchart.png",
            beforeAvg=before_avg,
            afterAvg=after_avg,
            changePercent=change_percent
        )

    except Exception as e:
        return BarChartResponse(
            result=False,
            message=str(e)
        )

app.include_router(router)
