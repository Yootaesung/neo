import json, urllib.request, datetime, math
import pandas as pd
import xml.etree.ElementTree as ET
import os.path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.relpath('./')))
secret_file = os.path.join(BASE_DIR, '../../secret.json')

with open(secret_file) as f:
    secrets = json.loads(f.read())

def get_secret(setting, secrets=secrets):
    try:
        return secrets[setting]
    except KeyError:
        errorMsg = "Set the {} environment variable.".format(setting)
        return errorMsg
        
def getRequestUrl(url):
    req = urllib.request.Request(url)
    try:
        response = urllib.request.urlopen(req)
        if response.getcode() == 200:
            return response.read().decode('utf-8')
    except Exception as e:
        # print(e)
        print("[%s] Error for URL : %s" % (datetime.datetime.now(), url))
        return None

def getBicycleData(pageNo, numOfRows):
    end_point = 'http://apis.data.go.kr/6310000/ulsanbicyclepath/getUlsanbicyclepathList'

    parameters = '?'
    parameters += "ServiceKey=" + get_secret("data_apiKey")
    parameters += "&pageNo=" + str(pageNo) 
    parameters += "&numOfRows=" + str(numOfRows) 
    url = end_point + parameters

    print('URL')
    print(url)

    result = getRequestUrl(url)
    if (result == None):
        return None
    else:
        return result

dataList = []

pageNo = 1 
numOfRows = 2 
nPage = 0

while(True):
    print('pageNo : %d, nPage : %d' % (pageNo, nPage))
    xmlData = getBicycleData(pageNo, numOfRows)
    print(xmlData)
    xmlTree = ET.fromstring(xmlData)
