import numpy as np
from pandas import DataFrame, Series

mydata = [[10.00, np.nan, 20.00],
          [20.00, 30.00, 40.00],
          [np.nan, np.nan, np.nan],
          [40.00, 50.00, 60.00]]
myindex = ['이순신', '김유신', '윤봉길', '계백']
mycolumns = ['국어', '영어', '수학']

myframe = DataFrame(mydata, index=myindex, columns=mycolumns)
print('\m 성적 데이터프레임 출력')
print(myframe)
print('-' * 50)

print('\n 집계함수는 기본적으로 NaN은 제외하고 연산')
print('\n sum(), axis=0, 열방향')
print(myframe.sum(axis=0))
print('-' * 50)

print('\n sum(), axis=1, 행방향')
print(myframe.sum(axis=1))
print('-' * 50)

print('\n mean(), axis=0, skipna=False')
print(myframe.mean(axis=0, skipna=False))
print('-' * 50)

print('\n mean(), axis=0, skipna=True')
print(myframe.mean(axis=0, skipna=True))
print('-' * 50)

print('\n idxmin() 최대값 색인 출력')
print(myframe.idxmin(axis=0))
print('-' * 50)

print('\n idxmax() 최소값 색인 출력')
print(myframe.idxmax(axis=0))
print('-' * 50)

print('\n 원본 데이터프레임')
print(myframe)
print('-' * 50)

print('\n cumsum(), axis=0, 열방향')
print(myframe.cumsum(axis=0))
print('-' * 50)

print('\n cumsum(), axis=1, 행방향')
print(myframe.cumsum(axis=1))
print('-' * 50)

print('\n cummax(), axis=1')
print(myframe.cummax(axis=1))
print('-' * 50)

print('\n cummin(), axis=1')
print(myframe.cummin(axis=1))
print('-' * 50)

print('\n 평균')
print(np.floor(myframe.mean()))
print('-' * 50)

print('\n 원본 데이터프레임')
print(myframe)
print('-' * 50)

myframe.loc[myframe['국어'].isnull(), '국어'] = np.min(myframe['국어']) - 5
myframe.loc[myframe['영어'].isnull(), '영어'] = np.min(myframe['영어']) - 5
myframe.loc[myframe['수학'].isnull(), '수학'] = np.min(myframe['수학']) - 5
print(myframe)
print('-' * 50)

print(np.round(myframe.describe()))