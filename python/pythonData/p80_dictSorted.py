wordinfo = {'세탁기':50, '선풍기':30, '냉장고':60}

myxticks = sorted(wordinfo, key=wordinfo.get, reverse=True)
print(myxticks)

reversed_key = sorted(wordinfo.keys(), reverse=True)
print(reversed_key)

chardata = sorted(wordinfo.values(), reverse=True)
print(chardata)

