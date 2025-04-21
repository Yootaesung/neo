import requests
import json
import pandas as pd
from datetime import datetime
import os.path
import xml.etree.ElementTree as ET
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List

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

class ExcluUseArItem(BaseModel):
    """Exclusive use area information"""
    exclusiveArea: str

class ExcluUseArResponse(BaseModel):
    """Exclusive use area search response"""
    result: bool
    resultCount: int
    exclusiveAreaList: List[ExcluUseArItem]

app = FastAPI()

@app.get('/getexcluusear')
async def GetExcluUseAr(
    bubjungdongCode: str = Query(
        ...,
        title="법정동코드",
        description="법정동코드 5자리를 입력하세요",
        min_length=5,
        max_length=5
    ),
    apartmentName: str = Query(
        ...,
        title="아파트명",
        description="검색할 아파트명을 입력하세요",
        min_length=1
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
            
            # items/item에서 해당 아파트 검색
            items = root.findall('.//item')
            
            if not items:
                return ExcluUseArResponse(
                    result=False,
                    resultCount=0,
                    exclusiveAreaList=[]
                )
            
            # 해당 아파트의 전용면적 목록 추출
            areas = []
            for item in items:
                apt_nm = item.find('aptNm')
                exclu_area = item.find('excluUseAr')
                
                if apt_nm is not None and exclu_area is not None:
                    if apt_nm.text == apartmentName:  # 입력받은 아파트 이름과 일치하는 경우
                        areas.append(float(exclu_area.text))
            
            if not areas:
                return ExcluUseArResponse(
                    result=False,
                    resultCount=0,
                    exclusiveAreaList=[]
                )
            
            # 중복 제거하고 정렬
            unique_areas = sorted(list(set(areas)))
            
            exclu_items = [ExcluUseArItem(exclusiveArea=str(area)) for area in unique_areas]
            return ExcluUseArResponse(
                result=True,
                resultCount=len(exclu_items),
                exclusiveAreaList=exclu_items
            )
            
        except ET.ParseError as pe:
            return {"오류": f"XML 파싱 오류: {str(pe)}"}
            
            # 모든 아파트 이름 추출
            apt_names = [item.find('aptNm').text for item in items if item.find('aptNm') is not None]
            return {"아파트_목록": apt_names}
            
        except ET.ParseError as pe:
            return {"오류": f"XML 파싱 오류: {str(pe)}"}
            
    except requests.exceptions.RequestException as e:
        return {"오류": f"API 요청 실패: {str(e)}"}
    
        