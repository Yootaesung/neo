from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from io import BytesIO
from fastapi.responses import StreamingResponse

JSON_SERVER_URL = "http://localhost:5000/beobjeongdong"

class BjdResponse(BaseModel):
    name: str
    status: str 
    code: str = None

plt.rcParams['font.family'] = 'NanumBarunGothic'
plt.rcParams['axes.unicode_minus'] = False

app = FastAPI()

SERVICE_KEY = "BEnu57CEJvi9WccFDSthV6KhaiqCbVpj111B1/eJno9YkXa7FkB4M3XFu9lGQZTrtDvLk+Xed3pUkxU9+lHQlQ=="

def fetch_data(lawd_cd, year, month):
    deal_ymd = f"{year}{month:02d}"
    params = {
        "serviceKey": SERVICE_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "pageNo": 1,
        "numOfRows": 1000
    }
    try:
        response = requests.get("http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev", params=params)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        items = root.find("body/items")
        if items is None:
            return []
        results = []
        for item in items.findall("item"):
            try:
                results.append({
                    "법정동코드": lawd_cd,
                    "단지명": item.findtext("aptNm"),
                    "전용면적": float(item.findtext("excluUseAr", 0)),
                    "거래금액(만원)": int(item.findtext("dealAmount").replace(",", "")),
                    "건축년도": int(item.findtext("buildYear")),
                    "계약일": f"{item.findtext('dealYear')}-{int(item.findtext('dealMonth')):02d}-{int(item.findtext('dealDay')):02d}",
                    "층": int(item.findtext("floor")),
                })
            except:
                continue
        return results
    except Exception as e:
        print(f"⚠️ 요청 실패: {lawd_cd} {deal_ymd} - {e}")
        return []

@app.get("/법정동코드찾기(전체)", response_model=List[BjdResponse])
async def 전체코드_검색(query: str = Query(..., description="지역 입력")):
    response = requests.get(JSON_SERVER_URL)
    data = response.json()

    results = []
    for item in data:
        if "\ufeff법정동코드" in item:
            item["법정동코드"] = item.pop("\ufeff법정동코드")
        if query in item["법정동명"]:
            status = "폐지" if item["폐지여부"] == "폐지" else "존재"
            code = item.get("법정동코드")
            results.append(BjdResponse(name=item["법정동명"], status=status, code=code if status == "존재" else None))
    
    if not results:
        return [{"name": query, "status": "검색 결과 없음"}]
    
    return results

@app.get("/법정동코드찾기(5자리)", response_model=List[BjdResponse])
async def 지역구입력(query: str = Query(..., description="지역 입력")):
    response = requests.get(JSON_SERVER_URL)
    data = response.json()

    results = []
    for item in data:
        if "\ufeff법정동코드" in item:
            item["법정동코드"] = item.pop("\ufeff법정동코드")
        if query in item["법정동명"] and item["폐지여부"] == "존재":
            full_code = item.get("법정동코드")
            code = full_code[:5] if full_code else None
            results.append(BjdResponse(name=item["법정동명"], status="존재", code=code))

    if not results:
        return [{"name": query, "status": "검색 결과 없음"}]

    return results

@app.get("/아파트검색")
async def 아파트목록(code: str = Query(..., description="법정동코드 (5자리)")):
    all_data = []
    for year in range(2020, 2024):
        for month in range(1, 13):
            data = fetch_data(code, year, month)
            all_data.extend(data)

    df = pd.DataFrame(all_data)
    if df.empty:
        return {"message": "해당 법정동코드에 대한 데이터 없음"}

    apt_names = sorted(df["단지명"].unique().tolist())
    return {"아파트 목록": apt_names}

@app.get("/전용면적검색")
async def 전용면적목록(
    code: str = Query(..., description="법정동코드 (5자리)"),
    apt: str = Query(..., description="아파트명")
):
    all_data = []
    for year in range(2020, 2024):
        for month in range(1, 13):
            data = fetch_data(code, year, month)
            all_data.extend(data)

    df = pd.DataFrame(all_data)
    if df.empty:
        return {"message": "해당 지역에 대한 데이터 없음"}

    areas = sorted(df[df["단지명"] == apt]["전용면적"].unique().tolist())
    return {"전용면적 목록": areas}

@app.get("/층검색")
async def 층목록(
    code: str = Query(..., description="법정동코드 (5자리)"),
    apt: str = Query(..., description="아파트명"),
    area: float = Query(..., description="전용면적")
):
    all_data = []
    for year in range(2020, 2024):
        for month in range(1, 13):
            data = fetch_data(code, year, month)
            all_data.extend(data)

    df = pd.DataFrame(all_data)
    if df.empty:
        return {"message": "해당 지역에 대한 데이터 없음"}

    floors = sorted(df[(df["단지명"] == apt) & (df["전용면적"] == area)]["층"].unique().tolist())
    return {"층 목록": floors}

@app.get("/실거래분석")
async def analyze_deals(
    code: str = Query(..., description="법정동코드 (5자리)"),
    apt: str = Query(..., description="아파트명"),
    area: float = Query(..., description="전용면적"),
    floor: int = Query(..., description="층"),
):
    all_data = []
    for year in range(2013, 2024):
        for month in range(1, 13):
            data = fetch_data(code, year, month)
            for d in data:
                d["계약일"] = pd.to_datetime(d["계약일"], errors="coerce")
            all_data.extend(data)

    df = pd.DataFrame(all_data)
    if df.empty:
        return {"message": "데이터 없음"}

    df_filtered = df[(df["단지명"] == apt) & (df["전용면적"] == area) & (df["층"] == floor)].copy()

    if df_filtered.empty:
        return {"message": "조건에 맞는 데이터 없음"}

    df_filtered["거래금액(만원)"] = pd.to_numeric(df_filtered["거래금액(만원)"], errors="coerce")
    df_filtered["연월"] = df_filtered["계약일"].dt.to_period("M").dt.to_timestamp()
    monthly = df_filtered.groupby("연월", observed=True)["거래금액(만원)"].mean().reset_index()
    monthly = monthly.set_index("연월").resample("MS").mean().interpolate(method="linear").reset_index()

    plt.figure(figsize=(14, 6))
    sns.lineplot(data=monthly, x="연월", y="거래금액(만원)")
    plt.title(f"{apt} 월별 평균 거래금액 추이")
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")