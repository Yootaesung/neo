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
