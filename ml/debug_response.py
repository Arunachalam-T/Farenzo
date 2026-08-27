import requests, json

cookies = {
    'rbuuid': 'ca34d1d0-842d-11f1-8a27-831578cf5b15',
    'mriClientId': 'BRca34d1d1-842d-11f1-8a27-831578cf5b15',
    'mriSessionId': 'BR9ff7df50-a23e-11f1-a84d-ebe8e11fb442',
    'env': 'PROD',
    'buildVersion': 'PROD_be1f247576',
    'funnelVariant': 'RESPONSIVE',
    'channel': 'MWEB',
    'country': 'IND',
    'currency': 'INR',
    'bm_sz': '32D2751E7E9FE86DBE8AA16BB9513958~YAAQjkU5Fy+vnUKgAQAAUSlSRAB4fLDX8UCwSH4pSvi/23VcEAa2tLViJFlufX3IsZRZtOUST/y9KiYLynNHUyxQSQNEHqvlm7pCHHG1FooUSdJdT9Wu52Ap1bhYhNLQXYKxYnBao9dUmIrjoSPqQhbMsO8xU6JIcDkC1jk+CEK1Tx14+6ItSZqrWVNwQjo7mEP7v5ZfE67maWg2tNtSk3rjHZWE4U8ultbSB6Lx6qUzgTfWFStzqVu13X79o0T8MT8+rz3C5lMc1K8G+P5C8uGEujeQk7VcgMeiGrdAoyoEe9FnJtRs2KoieF+XYHS92FxtuW7l7c8ukBLqJFv7uSm9ZCf+vYV0eIgH8SYJLLWJw/rPRdIayl60EldNp9YNL29KkEp+wJtQQjn9WD+ez3Yc77GMlu9snSF+cDnzuj8chcZn8ORtxxFX9jm5z7E8d8ER4g==~3752772~3753013',
}
headers = {
    'accept': '*/*',
    'content-type': 'application/json',
    'origin': 'https://www.redbus.in',
    'user-agent': 'Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Mobile Safari/537.36',
    'referer': 'https://www.redbus.in/bus-tickets/coimbatore-to-madurai?fromCityId=141&toCityId=126&onward=28-Aug-2026',
}
params = {
    'fromCity': '141', 'toCity': '126', 'DOJ': '28-Aug-2026',
    'limit': '10', 'offset': '0', 'meta': 'true',
    'groupId': '0', 'sectionId': '0', 'sort': '0', 'sortOrder': '0',
    'from': 'initialLoad', 'getUuid': 'true', 'bT': '1',
    'clearLMBFilter': 'undefined', 'isFilterApplied': 'false',
}
json_data = {
    'appliedFilterCount': 0,
    'onlyShow': [], 'dt': [], 'SeaterType': [], 'AcType': [],
    'travelsList': [], 'amtList': [], 'bpList': [], 'dpList': [],
    'CampaignFilter': [], 'at': [], 'persuasionList': [],
    'bpIdentifier': [], 'dpIdentifier': [], 'bcf': [],
    'opBusTypeFilterList': [], 'priceRange': [], 'RouteIds': [],
    'bpKeys': [], 'dpKeys': [], 'streaksFilter': [],
    'preRouteFilters': None,
}

session = requests.Session()
session.cookies.update(cookies)
session.headers.update(headers)
session.get('https://www.redbus.in', timeout=10)
r = session.post('https://www.redbus.in/rpw/api/searchResults', params=params, json=json_data, timeout=15)
data = r.json()

# Drill into 'data'
inner = data['data']
print('data keys:', list(inner.keys()))

for key in list(inner.keys()):
    val = inner[key]
    if isinstance(val, list) and len(val) > 0:
        first = val[0]
        if isinstance(first, dict):
            print(f'[{key}] = list of {len(val)} items')
            print(f'  First item keys: {list(first.keys())}')
            # Try to get operator name and fare
            name = first.get('travelsName') or first.get('nm') or first.get('name') or 'N/A'
            fare = first.get('fare') or first.get('minFare') or first.get('fares') or 'N/A'
            print(f'  Sample operator: {name}, fare: {fare}')
        else:
            print(f'[{key}] = list of {len(val)} items (not dicts): {val[0]}')
    elif isinstance(val, list):
        print(f'[{key}] = EMPTY list')
    elif isinstance(val, dict):
        print(f'[{key}] = dict, keys: {list(val.keys())[:8]}')
        # If it's metaData, print it
        if key == 'metaData':
            print(f'  metaData = {val}')
    else:
        print(f'[{key}] = {str(val)[:100]}')
