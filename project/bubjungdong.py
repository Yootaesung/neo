from fastapi import FastAPI, Query
from bson.objectid import ObjectId
from database import client

app = FastAPI()

mydb = client["bubjungdong"]
mycol = mydb["bubjungdong"]

@app.get('/getbubjungdong')
async def GetBubjungdong(
    dong: str = Query(
        None,
        title="법정동",
        description="검색할 법정동명을 입력하세요",
        min_length=1
    )
):
    if dong is None:
        return {"오류": "법정동을 입력하세요"}
    query = {
        "법정동명": {"$regex": dong, "$options": "i"},
        "폐지여부": {"$ne": "폐지"}
    }
    items = list(mycol.find(query, {"_id": 0, "법정동코드": 1, "법정동명": 1, "폐지여부": 1}))
    if items:
        # 법정동 코드를 앞 5글자만 남기고 결과 반환
        response_dict = {
            "result": True,
            "resultCount": len(items)
        }
        
        for i, item in enumerate(items):
            code = str(item["법정동코드"])[:5]
            response_dict[str(i)] = {
                "bubjungdongCode": code,
                "bubjungdongName": item["법정동명"],
                "exitOrNot": item["폐지여부"]
            }
        
        return response_dict
    return {
        "result": False,
        "resultCount": 0
    }
