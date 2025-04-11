import requests
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from time import sleep
from datetime import datetime

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

SERVICE_KEY = "BEnu57CEJvi9WccFDSthV6KhaiqCbVpj111B1/eJno9YkXa7FkB4M3XFu9lGQZTrtDvLk+Xed3pUkxU9+lHQlQ=="

REGION_TO_LAWD = {
    "경산시": "47290", "달서구": "27260", "파주시": "41390", "용인시": "41460",
    "강남구": "11680", "중구": "11140", "수원시": "41110", "부천시": "41190",
    "김포시": "41570", "시흥시": "41390", "구리시": "41310", "남양주시": "41360",
    "성남시": "41130", "마포구": "11440", "부평구": "28260", "남동구": "28170",
    "화성시": "41590", "광주광역시": "29110", "울산광역시": "31110", "대구광역시": "27110",
    "대전광역시": "30110", "인천광역시": "28110", "관악구": "11320", "강서구": "11500",
    "처인구": "41463", "분당구": "41135", "영통구": "41117"
}

SUBWAY_DATA = [
    (2024, "다산역", "남양주시"), (2024, "동구릉역", "구리시"),
    (2024, "장자호수공원역", "구리시"), (2024, "운정중앙역", "파주시"),
    (2024, "서울역 GTX-A", "중구"), (2024, "구성역", "용인시"),
    (2024, "수서역 GTX-A", "강남구"), (2023, "원종역", "부천시"),
    (2022, "신림선", "관악구"), (2019, "김포공항역", "강서구"),
    (2019, "운양역", "김포시"), (2018, "시흥시청역", "시흥시"),
    (2016, "운연역", "남동구"), (2016, "광교역", "영통구"),
    (2013, "전대·에버랜드역", "처인구"), (2012, "부평구청역", "부평구"),
    (2011, "정자역", "분당구"), (2010, "서동탄역", "화성시"),
    (2009, "신논현역", "강남구"), (2007, "공덕역", "마포구"),
    (2024, "하양역", "경산시"), (2024, "경산중앙역", "경산시"),
    (2022, "월배역", "달서구"), (2021, "안심~하양 연장", "대구광역시"),
    (2015, "대구 3호선", "대구광역시"), (2012, "광주송정역", "광주광역시"),
    (2011, "증심사입구역", "광주광역시"), (2010, "부산 4호선", "부산광역시"),
    (2009, "울산역", "울산광역시"), (2008, "광주 1호선", "광주광역시"),
    (2006, "대전 1호선", "대전광역시")
]

POLICIES = [
    ("2017-06-19", "정책"), ("2018-09-13", "정책"),
    ("2019-12-16", "정책"), ("2020-06-17", "정책"),
    ("2020-07-10", "정책"), ("2025-01-01", "정책")
]

ELECTIONS = [
    ("2017-05-09", "대통령 선거"),
    ("2020-04-15", "국회의원 선거"),
    ("2022-03-09", "대통령 선거"),
    ("2024-04-10", "국회의원 선거")
]

INTEREST_RATES = [
    ("2017-11-30", "인상"), ("2018-11-30", "인상"), ("2019-07-18", "인하"),
    ("2020-03-16", "인하"), ("2022-01-14", "인상"), ("2022-07-13", "인상"),
    ("2022-10-12", "인상"), ("2023-01-13", "인상")
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

def run_analysis(station_name, region_name, open_year):
    lawd_cd = REGION_TO_LAWD.get(region_name)
    if not lawd_cd:
        print(f"❌ LAWD 코드 없음: {region_name}")
        return

    start_year = min(open_year - 3, 2017)
    end_year = open_year + 1
    open_date = datetime(open_year, 3, 1)
    policy_dates = [datetime.strptime(p[0], "%Y-%m-%d") for p in POLICIES]
    election_dates_pres = [datetime.strptime(e[0], "%Y-%m-%d") for e in ELECTIONS if e[1] == "대통령 선거"]
    election_dates_parl = [datetime.strptime(e[0], "%Y-%m-%d") for e in ELECTIONS if e[1] == "국회의원 선거"]
    interest_rate_events = [(datetime.strptime(i[0], "%Y-%m-%d"), i[1]) for i in INTEREST_RATES]

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

    def label_period(d):
        if d < datetime(open_year - 2, 1, 1):
            return "개통 전"
        elif d < open_date:
            return "공사 중"
        else:
            return "개통 후"

    df["시기"] = df["계약일"].apply(label_period)
    df.to_csv(f"{station_name}_아파트거래.csv", index=False, encoding="utf-8-sig")
    print(f"📁 저장 완료: {station_name}_아파트거래.csv")

    plt.figure(figsize=(8, 5))
    sns.barplot(data=df, x="시기", y="거래금액(만원)", estimator="mean", palette="Set2")
    plt.title(f"{station_name} 개통 시기별 평균 거래금액")
    plt.tight_layout()
    plt.savefig(f"{station_name}_bar.png")
    plt.close()

    df["연월"] = df["계약일"].dt.to_period("M").astype(str)
    monthly = df.groupby("연월")["거래금액(만원)"].mean().reset_index()
    monthly = monthly.sort_values(by="연월")

    plt.figure(figsize=(14, 6))
    sns.lineplot(data=monthly, x="연월", y="거래금액(만원)")
    plt.axvline(open_date.strftime("%Y-%m"), color="red", linestyle="--", label="지하철 개통")
    for i, p in enumerate(policy_dates):
        plt.axvline(p.strftime("%Y-%m"), color="blue", linestyle=":", label="정부정책" if i == 0 else "")
    for i, e in enumerate(election_dates_pres):
        plt.axvline(e.strftime("%Y-%m"), color="green", linestyle="-.", label="대통령 선거" if i == 0 else "")
    for i, e in enumerate(election_dates_parl):
        plt.axvline(e.strftime("%Y-%m"), color="lime", linestyle="-.", label="국회의원 선거" if i == 0 else "")
    for i, (d, t) in enumerate(interest_rate_events):
        color = "black" if t == "인상" else "gray"
        style = "-" if t == "인상" else "--"
        plt.axvline(d.strftime("%Y-%m"), color=color, linestyle=style, label=f"금리 {t}" if i == 0 else "")
    plt.title(f"{station_name} 월별 거래금액 추이")
    plt.xticks(rotation=45, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{station_name}_line.png")
    plt.close()

if __name__ == "__main__":
    for year, station, region in SUBWAY_DATA:
        run_analysis(station, region, year)
