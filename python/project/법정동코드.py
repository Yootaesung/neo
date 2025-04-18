import pandas as pd
from pymongo import MongoClient
import json
import os

# 🔐 시크릿 키 불러오기
secret_path = '/work/neo/secret.json'
with open(secret_path, encoding='utf-8') as f:
    secrets = json.load(f)

# 🔐 MongoDB Atlas 접속 정보
username = secrets["ATLAS_Username"]
password = secrets["ATLAS_Password"]
hostname = secrets["ATLAS_Hostname"]

# ✅ 접속 URI 구성 (MongoDB Atlas)
mongo_uri = f"mongodb+srv://{username}:{password}@{hostname}?retryWrites=true&w=majority"

# ✅ MongoDB 연결
client = MongoClient(mongo_uri)
db = client["행정DB"]
collection = db["법정동"]

# ✅ CSV 파일 경로
csv_path = '/work/neo/python/project/법정동코드_전체.csv'

# ✅ CSV 읽기
df = pd.read_csv(csv_path, encoding='utf-8')
print(df)
# # ✅ DataFrame → 딕셔너리 목록
# records = df.to_dict(orient='records')
#
# # ✅ 기존 데이터 삭제 후 삽입
# collection.delete_many({})
# collection.insert_many(records)
#
# print(f"✅ 총 {len(records)}건의 법정동 정보가 MongoDB Atlas에 저장되었습니다.")
