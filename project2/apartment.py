import requests
import json
from datetime import datetime, timedelta
import os.path
import xml.etree.ElementTree as ET
from fastapi import FastAPI, Query, APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
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
router = APIRouter()

# 단일 사용자용 임시 DataFrame(리스트)
# (전역 변수 제거)

class ApartmentItem(BaseModel):
    apartmentName: str
    tradeCount: int

class ApartmentResponse(BaseModel):
    result: bool
    resultCount: int
    results: List[ApartmentItem]
    message: str = None

# 내부 함수: 위치(행정구역명)로부터 법정동코드 조회
import httpx
async def get_bubjungdong_code(location: str) -> str:
    url = "http://localhost:8000/bubjungdong/getbubjungdongcode"
    params = {"location": location}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        data = resp.json()
        if data.get("result"):
            return data["bubjungdongCode"]
        else:
            raise ValueError(data.get("message", "법정동코드 조회 실패"))

@router.get('/getapartment_by_code')
async def GetApartmentByCode(
    bubjungdongCode: str = Query(..., title="법정동코드", description="법정동코드 5자리 입력"),
    openDate: str = Query(..., title="개통일", description="지하철 개통일 8자리(YYYYMMDD)", min_length=8, max_length=8)
):
    try:
        # 캐시 컬렉션에서 정확히 일치하는 데이터만 반환
        cache_col = client["apartment"]["apartment_cache"]
        cache_doc = cache_col.find_one({"bubjungdongCode": bubjungdongCode, "openDate": openDate})
        if cache_doc and "results" in cache_doc:
            return {
                "result": True,
                "resultCount": len(cache_doc["results"]),
                "data": cache_doc["results"]
            }
        # 캐시에 없으면 외부 API에서 직접 데이터 수집 시도
        # 1. 외부 API 요청 (공공데이터포털)
        from datetime import datetime, timedelta
        import requests
        import xml.etree.ElementTree as ET
        items = []
        try:
            open_date = datetime.strptime(openDate, "%Y%m%d")
            start_date = open_date.replace(day=1) - timedelta(days=3*365)
            end_date = open_date.replace(day=1) + timedelta(days=3*365)
            url = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'
            current_date = start_date
            while current_date <= end_date:
                deal_ymd = current_date.strftime("%Y%m")
                params = '?serviceKey=' + get_secret("data_apiKey")
                params += '&LAWD_CD=' + bubjungdongCode[:5]
                params += '&DEAL_YMD=' + deal_ymd
                params += '&pageNo=1&numOfRows=100'
                url_with_params = url + params
                try:
                    response = requests.get(url_with_params)
                    root = ET.fromstring(response.content)
                    for item in root.findall('.//item'):
                        try:
                            deal_amount_node = item.find('거래금액')
                            deal_year_node = item.find('년')
                            deal_month_node = item.find('월')
                            apt_name_node = item.find('아파트') or item.find('aptNm')
                            if None in [deal_amount_node, deal_year_node, deal_month_node, apt_name_node]:
                                continue
                            deal_amount = deal_amount_node.text.replace(",", "").strip()
                            deal_year = deal_year_node.text.strip()
                            deal_month = deal_month_node.text.strip().zfill(2)
                            deal_day = item.find('일').text.strip().zfill(2) if item.find('일') is not None else "01"
                            apt_name = apt_name_node.text.strip()
                            road_name = item.find('도로명').text.strip() if item.find('도로명') is not None else ""
                            items.append({
                                "apartmentName": apt_name,
                                "dealAmount": deal_amount,
                                "dealDate": f"{deal_year}-{deal_month}-{deal_day}",
                                "roadName": road_name
                            })
                        except Exception as e:
                            print(f"데이터 파싱 오류: {e}")
                except Exception as e:
                    print(f"API 요청/파싱 오류: {e}")
                # 다음 달로 이동
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year+1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month+1)
            # 캐시에 저장
            cache_col.update_one(
                {"bubjungdongCode": bubjungdongCode, "openDate": openDate},
                {"$set": {"results": items}}, upsert=True
            )
            return {
                "result": True,
                "resultCount": len(items),
                "data": items,
                "message": "외부 API에서 데이터를 수집하여 반환합니다."
            }
        except Exception as e:
            return {
                "result": False,
                "resultCount": 0,
                "data": [],
                "message": f"외부 API 수집 실패: {str(e)}"
            }
    except Exception as e:
        return {"result": False, "message": str(e)}

        global current_apartment_df
        current_apartment_df = items
        print(f"[DF SAVE] current_apartment_df 저장: {len(current_apartment_df)}건")
        # 2. 수집 결과를 캐시에 저장
        cache_col.update_one(
            {"bubjungdongCode": bubjungdongCode, "openDate": openDate},
            {"$set": {"results": items}}, upsert=True
        )
        return {
            "result": True,
            "resultCount": len(items),
            "results": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/getapartment')
async def GetApartment(
    station: str = Query(
        ..., title="지하철역명", description="지하철역명을 입력하세요."),
    openDate: str = Query(
        ..., title="개통일", description="지하철 개통일을 8자리 숫자로 입력하세요.", min_length=8, max_length=8)
):
    try:
        # 1. subway DB에서 역명으로 위치(행정구역명) 조회
        mydb = client["subway"]
        subway_col = mydb["subway"]
        doc = subway_col.find_one({"역명": station})
        if not doc:
            return {"result": False, "resultCount": 0, "results": [], "message": "지하철역 정보를 찾을 수 없습니다."}
        location = doc.get("위치", None)
        if not location:
            return {"result": False, "resultCount": 0, "results": [], "message": "역의 위치 정보가 없습니다."}
        # 2. 위치(행정구역명)로 법정동코드 조회
        try:
            bubjungdongCode = await get_bubjungdong_code(location)
        except Exception as e:
            return {"result": False, "resultCount": 0, "results": [], "message": f"법정동코드 조회 실패: {str(e)}"}
        # 3. 실거래가 API 호출 (openDate ±5년, LAWD_CD는 5자리)
        open_date = datetime.strptime(openDate, "%Y%m%d")
        start_date = open_date.replace(day=1) - timedelta(days=3*365)
        end_date = open_date.replace(day=1) + timedelta(days=3*365)
        url = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'
        items = []
        current_date = start_date
        while current_date <= end_date:
            deal_ymd = current_date.strftime("%Y%m")
            params = '?serviceKey=' + get_secret("data_apiKey")
            params += '&LAWD_CD=' + bubjungdongCode[:5]
            params += '&DEAL_YMD=' + deal_ymd
            params += '&pageNo=1&numOfRows=100'
            url_with_params = url + params
            try:
                response = requests.get(url_with_params)
                root = ET.fromstring(response.content)
                for item in root.findall('.//item'):
                    try:
                        # 필수 필드가 모두 존재하는지 확인
                        deal_amount_node = item.find('거래금액')
                        deal_year_node = item.find('년')
                        deal_month_node = item.find('월')
                        apt_name_node = item.find('아파트') or item.find('aptNm')
                        if None in [deal_amount_node, deal_year_node, deal_month_node, apt_name_node]:
                            continue  # 필수 값이 없으면 skip
                        deal_amount = deal_amount_node.text.replace(",", "").strip()
                        deal_year = deal_year_node.text.strip()
                        deal_month = deal_month_node.text.strip().zfill(2)
                        deal_day = item.find('일').text.strip().zfill(2) if item.find('일') is not None else "01"
                        apt_name = apt_name_node.text.strip()
                        road_name = item.find('도로명').text.strip() if item.find('도로명') is not None else ""
                        items.append({
                            "apartmentName": apt_name,
                            "dealAmount": deal_amount,
                            "dealDate": f"{deal_year}-{deal_month}-{deal_day}",
                            "roadName": road_name
                        })
                    except Exception as e:
                        print(f"데이터 파싱 오류: {e}")
            except Exception as e:
                print(f"API 요청/파싱 오류: {e}")
            # 다음 달로 이동
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year+1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month+1)
        # 도로명 필터링 없이, 법정동코드(LAWD_CD)로 가져온 모든 거래 데이터를 반환
        return {
            "result": True,
            "resultCount": len(items),
            "results": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from uuid import uuid4

STATIC_DIR = os.path.join(BASE_DIR, 'static')
IMAGE_DIR = os.path.join(STATIC_DIR, 'images')
os.makedirs(IMAGE_DIR, exist_ok=True)

# 라인그래프 생성 함수
async def create_line_graph(prices, months, open_date):
    plt.figure(figsize=(12, 6))
    plt.plot(months, prices, marker='o', color='royalblue', label='실거래가')
    plt.axvline(open_date, color='red', linestyle='--', label='개통일')
    plt.xlabel('거래월')
    plt.ylabel('실거래가(만원)')
    plt.title('개통 전후 실거래가 변화')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    # 파일 저장
    fname = f"line_{uuid4()}.png"
    fpath = os.path.join(IMAGE_DIR, fname)
    plt.savefig(fpath, dpi=200)
    plt.close()
    return f"/static/images/{fname}"

# 바그래프 생성 함수
async def create_bar_graph(prices, months, open_date, window):
    open_idx = months.index(open_date) if open_date in months else len(months)//2
    before = [p for m, p in zip(months, prices) if m < open_date]
    after = [p for m, p in zip(months, prices) if m >= open_date]
    before_mean = np.mean(before) if before else 0
    after_mean = np.mean(after) if after else 0
    plt.figure(figsize=(7, 6))
    bars = plt.bar(['개통 전', '개통 후'], [before_mean, after_mean], color=['blue', 'orange'])
    plt.title(f'개통 전후 {window}년 평균 실거래가')
    plt.ylabel('평균 실거래가(만원)')
    for bar in bars:
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{bar.get_height():.1f}',
                 ha='center', va='bottom', fontweight='bold')
    # 증감률 표시
    if before_mean > 0:
        diff_pct = (after_mean - before_mean) / before_mean * 100
        plt.text(0.5, max(before_mean, after_mean)*1.05, f'증감률: {diff_pct:+.1f}%',
                 ha='center', va='bottom', fontsize=12, color='purple')
    plt.tight_layout()
    fname = f"bar_{uuid4()}.png"
    fpath = os.path.join(IMAGE_DIR, fname)
    plt.savefig(fpath, dpi=200)
    plt.close()
    return f"/static/images/{fname}"

@router.get('/station_price_graph')
async def station_price_graph(
    station: str = Query(..., description="지하철역명"),
    window: int = Query(5, description="개통일 기준 ±N년 (기본 5년)")
):
    try:
        # 1. subway DB에서 역명으로 위치/개통일 조회
        mydb = client["subway"]
        subway_col = mydb["subway"]
        doc = subway_col.find_one({"역명": station})
        if not doc:
            raise HTTPException(status_code=404, detail="지하철역 정보를 찾을 수 없습니다.")
        location = doc.get("위치")
        open_date_str = doc.get("개통일")
        if not location or not open_date_str:
            raise HTTPException(status_code=404, detail="역의 위치 또는 개통일 정보가 없습니다.")
        open_date = datetime.strptime(open_date_str, "%Y%m%d")
        # 2. 위치로 법정동코드 조회
        bubjungdongCode = await get_bubjungdong_code(location)
        # 3. 실거래가 데이터 수집 (window년 범위)
        start_date = open_date - timedelta(days=window*365)
        end_date = open_date + timedelta(days=window*365)
        url = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'
        prices_by_month = {}
        current_date = start_date
        while current_date <= end_date:
            deal_ymd = current_date.strftime("%Y%m")
            params = '?serviceKey=' + get_secret("data_apiKey")
            params += '&LAWD_CD=' + bubjungdongCode
            params += '&DEAL_YMD=' + deal_ymd
            params += '&pageNo=1&numOfRows=100'
            url_with_params = url + params
            try:
                response = requests.get(url_with_params)
                root = ET.fromstring(response.content)
                for item in root.findall('.//item'):
                    price = int(item.find('거래금액').text.replace(",", "").strip())
                    ymd = item.find('년').text + item.find('월').text.zfill(2)
                    prices_by_month.setdefault(ymd, []).append(price)
            except Exception as e:
                print(f"데이터 수집 오류: {e}")
            current_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)
        if not prices_by_month:
            return {"result": False, "message": "거래 데이터가 없습니다."}
        # 월별 평균 계산
        months = sorted(prices_by_month.keys())
        prices = [np.mean(prices_by_month[m]) for m in months]
        # 4. 그래프 생성
        open_month = open_date.strftime("%Y%m")
        line_url = await create_line_graph(prices, months, open_month)
        bar_url = await create_bar_graph(prices, months, open_month, window)
        return {"result": True, "line_graph_url": line_url, "bar_graph_url": bar_url}
    except Exception as e:
        return {"result": False, "message": str(e)}

@router.get('/current_df')
def get_current_apartment_df():
    global current_apartment_df
    if current_apartment_df is not None:
        return {"result": True, "count": len(current_apartment_df), "data": current_apartment_df}
    else:
        return {"result": False, "message": "No data loaded"}

app.include_router(router)
