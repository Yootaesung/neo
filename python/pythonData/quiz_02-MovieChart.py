#!/usr/bin/env python

import urllib.request
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'NanumBarunGothic'

url = 'https://www.moviechart.co.kr/rank/boxoffice'
html = urllib.request.urlopen(url)
soup = BeautifulSoup(html, 'html.parser')

infos = soup.findAll('div', attrs={'class': 'listTable group1'})

mydata0 = [i for i in range(1, 20)]

result = []
title =soup.select("td.title")
for i in title:
    result.append(i.text.rstrip('\n'))
mydata1 = result

result = []
date =soup.select("td.date")
for i in date:
    result.append(i.text.text)
mydata2 = result

result = []
audience =soup.select("td.audience")
for i in audience:
    result.append(i.text.strip()[0:6])
mydata3 = result



myframe = DataFrame(mylist, columns=['제목', '평점', '예매율', '개봉일'])
filename = 'cgvMovie.csv'
myframe.to_csv(filename, encoding='utf-8', index=False)
print(filename, ' saved….')
print('\n# finished.')
