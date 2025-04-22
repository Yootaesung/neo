from fastapi import Request

class CommonParams:
    def __init__(self):
        self.bubjungdongCode = None
        self.apartmentName = None
        self.exclusiveArea = None
        self.floor = None
        self.openDate = None  # 개통일 추가

async def get_common_params(request: Request):
    if not hasattr(request.app, 'common_params'):
        request.app.common_params = CommonParams()
    return request.app.common_params

def update_common_params(common_params: CommonParams, **updates):
    for key, value in updates.items():
        if value is not None:  # None이 아닌 값만 업데이트
            setattr(common_params, key, value)
    return common_params
