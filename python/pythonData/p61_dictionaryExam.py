#!/usr/bin/env python

dictionary = {'김유신' : 50, '윤봉길' : 40, '김구' : 60}
print('Dictionary : ', dictionary)

for key in dictionary.keys():
    print(f'key : {key}')

for value in dictionary.values():
    print(f'value : {value}')

for key in dictionary.keys():
    print('{}의 나이는 {}입니다. '.format(key, dictionary[key]))

for key, value in dictionary.items():
    print(f'{key}의 나이는 {value}입니다. ')

findkey = ('유관순')

if findkey in dictionary.keys():
    print(f'{findkey}(은)는 존재합니다.')
else:
    print(f'{findkey}(은)는 존재하지 않습니다.')

result = dictionary.pop('김구')
print('After pop :', result)

dictionary.clear()
print('Dictionary lsit :', dictionary)