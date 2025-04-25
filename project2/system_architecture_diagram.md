# 시스템 구성도

## Subway MongoDB 데이터 예시

| 개통일           | 역명     | 위치                  | 소속 노선 | 역사도로명주소                          |
|------------------|----------|-----------------------|-----------|-----------------------------------------|
| 2011-10-28 0:00  | 강남역   | 서울특별시 강남구     | 신분당선  | 강남대로 지하396 (역삼동 858)           |

---

## 시스템 구성도 (Project2)

```mermaid
flowchart LR
    User[사용자]
    Node[Node.js\n(프론트엔드 서버)]
    API[FastAPI\n(백엔드 API)]
    DB[MongoDB\n(지하철/실거래가 데이터)]
    ExternalAPI[외부 API\n(공공데이터포털)]

    User <--> Node
    Node <--> API
    API <--> DB
    API <--> ExternalAPI
```

- **MongoDB**에는 위와 같은 지하철역 정보(개통일, 역명, 위치, 노선, 도로명주소 등)가 저장되어 있습니다.
- 사용자는 Node.js를 통해 FastAPI에 요청하고, FastAPI는 MongoDB에서 데이터를 조회하거나 외부 API에 요청합니다.
