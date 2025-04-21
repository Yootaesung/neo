import requests
import json
import pandas as pd
from datetime import datetime
import os.path
import xml.etree.ElementTree as ET
from fastapi import FastAPI, Query

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

@app.get('/getapartmentdata')
async def GetApartmentData(
    bubjungdongCode: str = Query(
        ...,
        title="법정동코드",
        description="법정동코드 5자리를 입력하세요",
        min_length=5,
        max_length=5
    )
):
    
    # 현재 년월을 YYYYMM 형식으로 설정
    current_date = datetime.now().strftime('%Y%m')
    
    url = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'
    
    params = '?serviceKey=' + get_secret("data_apiKey")
    params += '&LAWD_CD=' + bubjungdongCode
    params += '&DEAL_YMD=' + current_date
    params += '&pageNo=1'
    params += '&numOfRows=100'  

    url += params
    print(url)
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # HTTP 에러 처리
        
        # XML 파싱
        try:
            root = ET.fromstring(response.text)
            
            # items/item 에서 아파트 이름 추출
            items = root.findall('.//item')
            
            if not items:
                return {
                    "result": False,
                    "resultCount": 0
                }
            
            # 모든 아파트 이름 추출
            response_dict = {
                "result": True,
                "resultCount": 0
            }
            
            idx = 0
            for item in items:
                apt_nm = item.find('aptNm')
                if apt_nm is not None:
                    response_dict[str(idx)] = {
                        "apartmentName": apt_nm.text
                    }
                    idx += 1
            
            response_dict["resultCount"] = idx
            return response_dict
            
        except ET.ParseError as pe:
            return {"오류": f"XML 파싱 오류: {str(pe)}"}
            
    except requests.exceptions.RequestException as e:
        return {"오류": f"API 요청 실패: {str(e)}"}
    
        