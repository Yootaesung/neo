import requests
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from time import sleep
from datetime import datetime

plt.rcParams['font.family'] = 'NanumBarunGothic'
plt.rcParams['axes.unicode_minus'] = False

SERVICE_KEY = "BEnu57CEJvi9WccFDSthV6KhaiqCbVpj111B1/eJno9YkXa7FkB4M3XFu9lGQZTrtDvLk+Xed3pUkxU9+lHQlQ=="

REGION_TO_LAWD = {
    "송파구": "11710"
}

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
                    "법정동": item.findtext("umdNm"),
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

def run_analysis(station_name, region_name, open_year, apt_name, area, floor):
    lawd_cd = REGION_TO_LAWD.get(region_name)
    if not lawd_cd:
        print(f"❌ LAWD 코드 없음: {region_name}")
        return

    start_year = max(open_year - 5, 2010)
    end_year = open_year + 5
    open_date = datetime(open_year, 12, 1)

    all_data = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            print(f"[{station_name}] {year}-{month:02d} 수집 중...")
            data = fetch_data(lawd_cd, year, month)
            for d in data:
                d["계약일"] = pd.to_datetime(d["계약일"], errors="coerce")
                d["역이름"] = station_name
            all_data.extend(data)
            sleep(0.3)

    df = pd.DataFrame(all_data)
    if df.empty:
        print(f"⚠️ {station_name} 데이터 없음")
        return

    # 조건에 맞는 데이터만 필터링
    df_filtered = df[(df["단지명"] == apt_name) & (df["전용면적"] == area) & (df["층"] == floor)]

    if df_filtered.empty:
        print(f"⚠️ 조건에 맞는 데이터 없음: {apt_name}, {area}, {floor}")
        return

    def label_period(d):
        if d < datetime(open_year - 2, 1, 1):
            return "개통 전"
        elif d < open_date:
            return "공사 중"
        else:
            return "개통 후"

    df_filtered["시기"] = df_filtered["계약일"].apply(label_period)
    df_filtered.to_csv(f"{station_name}_{apt_name}_아파트거래.csv", index=False, encoding="utf-8-sig")
    print(f"📁 저장 완료: {station_name}_{apt_name}_아파트거래.csv")

    # 시기별 평균 거래금액 막대그래프
    plt.figure(figsize=(8, 5))
    sns.barplot(data=df_filtered, x="시기", y="거래금액(만원)", estimator="mean", palette="Set2")
    plt.title(f"{station_name} {apt_name} 개통 시기별 평균 거래금액")
    plt.tight_layout()
    plt.savefig(f"{station_name}_{apt_name}_bar.png")
    plt.close()

    # 월별 평균 거래금액 추이 그래프
    df_filtered["연월"] = df_filtered["계약일"].dt.to_period("M").astype(str)
    monthly = df_filtered.groupby("연월")["거래금액(만원)"].mean().reset_index()
    monthly = monthly.sort_values(by="연월")

    plt.figure(figsize=(14, 6))
    sns.lineplot(data=monthly, x="연월", y="거래금액(만원)")
    plt.axvline(open_date.strftime("%Y-%m"), color="red", linestyle="--", label="지하철 개통")
    plt.title(f"{station_name} {apt_name} 월별 거래금액 추이")
    plt.xticks(rotation=45, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{station_name}_{apt_name}_line.png")
    plt.close()

if __name__ == "__main__":
    run_analysis("석촌역", "송파구", 2018, "리센츠", 84.99, 23)
