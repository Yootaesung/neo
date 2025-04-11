import requests
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from time import sleep
from datetime import datetime

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

SERVICE_KEY = "BEnu57CEJvi9WccFDSthV6KhaiqCbVpj111B1/eJno9YkXa7FkB4M3XFu9lGQZTrtDvLk+Xed3pUkxU9+lHQlQ=="

REGION_TO_LAWD = {
    "Gyeongsan": "47290", "Dalseo": "27260", "Paju": "41390", "Yongin": "41460",
    "Gangnam": "11680", "Jung-gu": "11140", "Suwon": "41110", "Bucheon": "41190",
    "Gimpo": "41570", "Siheung": "41390", "Guri": "41310", "Namyangju": "41360",
    "Seongnam": "41130", "Mapo": "11440", "Bupyeong": "28260", "Namdong": "28170",
    "Hwaseong": "41590", "Gwangju": "29110", "Ulsan": "31110", "Daegu": "27110",
    "Daejeon": "30110", "Incheon": "28110", "Gwanak": "11320", "Gangseo": "11500",
    "Cheoin": "41463", "Bundang": "41135", "Yeongtong": "41117"
}

SUBWAY_DATA = [
    (2024, "Dasan", "Namyangju"), (2024, "Donggurung", "Guri"),
    (2024, "JangjaLakePark", "Guri"), (2024, "UnjeongCentral", "Paju"),
    (2024, "Seoul GTX-A", "Jung-gu"), (2024, "Guseong", "Yongin"),
    (2024, "Suseo GTX-A", "Gangnam"), (2023, "Wonjong", "Bucheon"),
    (2022, "Sillim Line", "Gwanak"), (2019, "Gimpo Airport", "Gangseo"),
    (2019, "Unyang", "Gimpo"), (2018, "SiheungCityHall", "Siheung"),
    (2016, "Unyeon", "Namdong"), (2016, "Gwanggyo", "Yeongtong"),
    (2013, "Everland", "Cheoin"), (2012, "Bupyeong-gu Office", "Bupyeong"),
    (2011, "Jeongja", "Bundang"), (2010, "Seodongtan", "Hwaseong"),
    (2009, "Sinnonhyeon", "Gangnam"), (2007, "Gongdeok", "Mapo"),
    (2024, "Hayang", "Gyeongsan"), (2024, "GyeongsanCentral", "Gyeongsan"),
    (2022, "Wolbae", "Dalseo"), (2021, "Ansim~Hayang", "Daegu"),
    (2015, "Daegu Line 3", "Daegu"), (2012, "Gwangju Songjeong", "Gwangju"),
    (2011, "Jeungsimsa", "Gwangju"), (2010, "Busan Line 4", "Busan"),
    (2009, "Ulsan", "Ulsan"), (2008, "Gwangju Line 1", "Gwangju"),
    (2006, "Daejeon Line 1", "Daejeon")
]

POLICIES = [
    ("2017-06-19", "Policy"), ("2018-09-13", "Policy"),
    ("2019-12-16", "Policy"), ("2020-06-17", "Policy"),
    ("2020-07-10", "Policy"), ("2025-01-01", "Policy")
]

ELECTIONS = [
    ("2017-05-09", "Presidential"),
    ("2020-04-15", "Parliamentary"),
    ("2022-03-09", "Presidential"),
    ("2024-04-10", "Parliamentary")
]

INTEREST_RATES = [
    ("2017-11-30", "Up"), ("2018-11-30", "Up"), ("2019-07-18", "Down"),
    ("2020-03-16", "Down"), ("2022-01-14", "Up"), ("2022-07-13", "Up"),
    ("2022-10-12", "Up"), ("2023-01-13", "Up")
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
                    "Location": item.findtext("umdNm"),
                    "Complex": item.findtext("aptNm"),
                    "Area(m²)": float(item.findtext("excluUseAr", 0)),
                    "Price(₩10k)": int(item.findtext("dealAmount").replace(",", "")),
                    "Built_Year": int(item.findtext("buildYear")),
                    "Contract_Date": f"{item.findtext('dealYear')}-{int(item.findtext('dealMonth')):02d}-{int(item.findtext('dealDay')):02d}",
                    "Floor": int(item.findtext("floor")),
                })
            except:
                continue
        return results
    except Exception as e:
        print(f"⚠️ Request failed: {lawd_cd} {deal_ymd} - {e}")
        return []

def run_analysis(station_name, region_name, open_year):
    lawd_cd = REGION_TO_LAWD.get(region_name)
    if not lawd_cd:
        print(f"❌ LAWD code not found for: {region_name}")
        return

    start_year = min(open_year - 3, 2017)
    end_year = open_year + 1
    open_date = datetime(open_year, 3, 1)
    policy_dates = [datetime.strptime(p[0], "%Y-%m-%d") for p in POLICIES]
    election_dates_pres = [datetime.strptime(e[0], "%Y-%m-%d") for e in ELECTIONS if e[1] == "Presidential"]
    election_dates_parl = [datetime.strptime(e[0], "%Y-%m-%d") for e in ELECTIONS if e[1] == "Parliamentary"]
    interest_rate_events = [(datetime.strptime(i[0], "%Y-%m-%d"), i[1]) for i in INTEREST_RATES]

    all_data = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            print(f"[{station_name}] {year}-{month:02d} collecting...")
            data = fetch_data(lawd_cd, year, month)
            for d in data:
                d["Contract_Date"] = pd.to_datetime(d["Contract_Date"], errors="coerce")
                d["Station"] = station_name
            all_data.extend(data)
            sleep(0.3)

    df = pd.DataFrame(all_data)
    if df.empty:
        print(f"⚠️ No data for {station_name}")
        return

    def label_period(d):
        if d < datetime(open_year - 2, 1, 1):
            return "Before"
        elif d < open_date:
            return "Under Construction"
        else:
            return "After"

    df["Phase"] = df["Contract_Date"].apply(label_period)
    df.to_csv(f"{station_name}_Apt_Trades.csv", index=False, encoding="utf-8-sig")
    print(f"📁 Saved: {station_name}_Apt_Trades.csv")

    plt.figure(figsize=(8, 5))
    sns.barplot(data=df, x="Phase", y="Price(₩10k)", estimator="mean", palette="Set2")
    plt.title(f"{station_name} Avg Price by Subway Phase")
    plt.tight_layout()
    plt.savefig(f"{station_name}_bar.png")
    plt.close()

    df["YearMonth"] = df["Contract_Date"].dt.to_period("M").astype(str)
    monthly = df.groupby("YearMonth")["Price(₩10k)"].mean().reset_index()
    monthly = monthly.sort_values(by="YearMonth")

    plt.figure(figsize=(14, 6))
    sns.lineplot(data=monthly, x="YearMonth", y="Price(₩10k)")
    plt.axvline(open_date.strftime("%Y-%m"), color="red", linestyle="--", label="Subway Opening")
    for i, p in enumerate(policy_dates):
        plt.axvline(p.strftime("%Y-%m"), color="blue", linestyle=":", label="Policy" if i == 0 else "")
    for i, e in enumerate(election_dates_pres):
        plt.axvline(e.strftime("%Y-%m"), color="green", linestyle="-.", label="Presidential" if i == 0 else "")
    for i, e in enumerate(election_dates_parl):
        plt.axvline(e.strftime("%Y-%m"), color="lime", linestyle="-.", label="Parliamentary" if i == 0 else "")
    for i, (d, t) in enumerate(interest_rate_events):
        color = "black" if t == "Up" else "gray"
        style = "-" if t == "Up" else "--"
        plt.axvline(d.strftime("%Y-%m"), color=color, linestyle=style, label=f"Rate {t}" if i == 0 else "")
    plt.title(f"{station_name} Monthly Price Trend")
    plt.xticks(rotation=45, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{station_name}_line.png")
    plt.close()

if __name__ == "__main__":
    for year, station, region in SUBWAY_DATA:
        run_analysis(station, region, year)

