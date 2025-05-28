import requests

where_values = 'nexearch'
sm_values = 'top_hty'
fbm_values = 1
ie_values = 'UTF-8'
query_values = 'python'

baseurl = 'https://search.naver.com/search.naver'
parameters = "?where={0}&sm={1}&fbm={2}&ie={3}&query={4}".format(where_values, sm_values, fbm_values, ie_values, query_values)

url_parameters = baseurl + parameters
res = requests.get(url_parameters)
print(res.url)
