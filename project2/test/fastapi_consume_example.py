import requests

# FastAPI 서버가 로컬에서 5001번 포트로 구동 중이라고 가정
BASE_URL = 'http://localhost:8000'

# 1. 지하철역 검색 예시 (지역명으로 검색)
def search_subway(region):
    resp = requests.get(f"{BASE_URL}/subway/search", params={"region": region})
    print("[지하철역 검색 결과]", resp.json())

# 2. 특정 지하철역 상세정보(개통일, 법정동코드 등)
def get_subway_detail(station_id):
    resp = requests.get(f"{BASE_URL}/subway/detail", params={"station_id": station_id})
    print("[지하철역 상세정보]", resp.json())

# 3. 법정동코드/개통일로 아파트 실거래가 요청
def get_apartment_deals(bubjungdongCode, openDate):
    resp = requests.get(f"{BASE_URL}/apartment/getapartment_by_code", params={"bubjungdongCode": bubjungdongCode, "openDate": openDate})
    print("[아파트 실거래가 결과]", resp.json())

# 4. 저장된 거래 데이터 일부만 확인 (limit)
def get_current_df(limit=10):
    resp = requests.get(f"{BASE_URL}/apartment/current_df", params={"limit": limit})
    print(f"[임시 df 일부({limit}건)]", resp.json())

if __name__ == "__main__":
    # 예시: 강남 지역 지하철역 검색
    search_subway("강남")

    # 예시: 특정 역 상세정보 (station_id는 실제 값으로 대체)
    get_subway_detail("123")

    # 예시: 법정동코드/개통일로 실거래가 요청
    get_apartment_deals("11680", "20131221")

    # 예시: 임시 df 일부만 확인
    get_current_df(5)
