from fastapi import FastAPI, Query
from bson.objectid import ObjectId
import pydantic
import pandas as pd
import json
from pymongo import MongoClient

# ObjectId -> str 자동 변환
pydantic.json.ENCODERS_BY_TYPE[ObjectId] = str

# MongoDB 연결
with open("/work/neo/secret.json", encoding="utf-8") as f:
    secrets = json.load(f)

atlas_host = secrets["ATLAS_Hostname"]
atlas_user = secrets["ATLAS_Username"]
atlas_pass = secrets["ATLAS_Password"]

mongo_uri = f"mongodb+srv://{atlas_user}:{atlas_pass}@{atlas_host}?retryWrites=true&w=majority"
client = MongoClient(mongo_uri)
mydb = client["test"]
mycol = mydb["법정동"]

app = FastAPI()

@app.get('/')
async def health_check():
    return {'status': 'ok'}

@app.get('/법정동목록')
async def get_bjd_list(limit: int = 10):
    result = list(mycol.find({}, {'_id': 0}).limit(limit))
    return result

@app.get('/법정동검색')
async def search_bjd(법정동명: str = Query(..., description="법정동명을 입력하세요")):
    result = list(mycol.find({'법정동명': {'$regex': 법정동명}}, {'_id': 0}))
    if result:
        return result
    return {'message': '검색 결과 없음'}
