import csv
import json

# CSV 파일 경로
csv_file = '법정동코드_전체.csv'

# 출력 JSON 파일 경로
json_file = 'beobjeongdong.json'

# 변환 작업
with open(csv_file, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    data = list(reader)

# json-server에서 사용할 수 있는 구조로 변환
output = {"법정동": data}

# JSON 저장
with open(json_file, mode='w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("변환 완료: db.json 생성됨")