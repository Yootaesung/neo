import requests
import xml.etree.ElementTree as ET
import pandas as pd
from time import sleep

SERVICE_KEY = "BEnu57CEJvi9WccFDSthV6KhaiqCbVpj111B1/eJno9YkXa7FkB4M3XFu9lGQZTrtDvLk+Xed3pUkxU9+lHQlQ=="
URL = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
START_YEAR = 2021
END_YEAR = 2024

# 전국 LAWD_CD 샘플 (실제는 260여개 — 필요하면 전체 제공 가능)
LAWD_CODES = [
    "47290",  # 경북 경산시
]

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
        response = requests.get(URL, params=params, timeout=5)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        items = root.find("body/items")
        if items is None:
            return []

        results = []
        for item in items.findall("item"):
            data = {
                "지역코드": lawd_cd,
                "법정동": item.findtext("umdNm"),
                "단지명": item.findtext("aptNm"),
                "전용면적": item.findtext("excluUseAr"),
                "거래금액(만원)": item.findtext("dealAmount"),
                "건축년도": item.findtext("buildYear"),
                "계약일": f"{item.findtext('dealYear')}-{item.findtext('dealMonth'):0>2}-{item.findtext('dealDay'):0>2}",
                "층": item.findtext("floor"),
            }
            results.append(data)
        return results

    except Exception as e:
        print(f"⚠️ {lawd_cd} {deal_ymd} 요청 실패: {e}")
        return []

def main():
    all_data = []
    for lawd_cd in LAWD_CODES:
        for year in range(START_YEAR, END_YEAR + 1):
            for month in range(1, 13):
                if year == END_YEAR and month > 12:
                    break
                print(f"[{lawd_cd}] {year}-{month:02d} 데이터 수집 중...")
                monthly_data = fetch_data(lawd_cd, year, month)
                all_data.extend(monthly_data)
                sleep(0.3)  # 요청 제한 방지

    df = pd.DataFrame(all_data)
    df.to_csv("apart_trade_gungsan.csv", index=False, encoding="utf-8-sig")
    print("✅ CSV 저장 완료: apart_trade_gungsan.csv")

if __name__ == "__main__":
    main()