import requests, json

cookies = {
    'rbuuid': 'ca34d1d0-842d-11f1-8a27-831578cf5b15',
    'mriSessionId': 'BR9ff7df50-a23e-11f1-a84d-ebe8e11fb442',
    'env': 'PROD', 'channel': 'MWEB', 'country': 'IND',
    'bm_sz': '32D2751E7E9FE86DBE8AA16BB9513958~YAAQjkU5Fy+vnUKgAQAAUSlSRAB4fLDX8UCwSH4pSvi/23VcEAa2tLViJFlufX3IsZRZtOUST/y9KiYLynNHUyxQSQNEHqvlm7pCHHG1FooUSdJdT9Wu52Ap1bhYhNLQXYKxYnBao9dUmIrjoSPqQhbMsO8xU6JIcDkC1jk+CEK1Tx14+6ItSZqrWVNwQjo7mEP7v5ZfE67maWg2tNtSk3rjHZWE4U8ultbSB6Lx6qUzgTfWFStzqVu13X79o0T8MT8+rz3C5lMc1K8G+P5C8uGEujeQk7VcgMeiGrdAoyoEe9FnJtRs2KoieF+XYHS92FxtuW7l7c8ukBLqJFv7uSm9ZCf+vYV0eIgH8SYJLLWJw/rPRdIayl60EldNp9YNL29KkEp+wJtQQjn9WD+ez3Yc77GMlu9snSF+cDnzuj8chcZn8ORtxxFX9jm5z7E8d8ER4g==~3752772~3753013',
}
headers = {
    'accept': '*/*', 'content-type': 'application/json',
    'origin': 'https://www.redbus.in',
    'user-agent': 'Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Mobile Safari/537.36',
    'referer': 'https://www.redbus.in/',
}
params = {'fromCity': '141', 'toCity': '126', 'DOJ': '05-Sep-2026',
          'limit': '5', 'offset': '0', 'meta': 'true',
          'groupId': '0', 'sectionId': '0', 'sort': '0', 'sortOrder': '0',
          'from': 'initialLoad', 'getUuid': 'true', 'bT': '1',
          'clearLMBFilter': 'undefined', 'isFilterApplied': 'false'}
json_data = {'appliedFilterCount': 0, 'onlyShow': [], 'dt': [], 'SeaterType': [],
             'AcType': [], 'travelsList': [], 'amtList': [], 'bpList': [], 'dpList': [],
             'CampaignFilter': [], 'at': [], 'persuasionList': [], 'bpIdentifier': [],
             'dpIdentifier': [], 'bcf': [], 'opBusTypeFilterList': [], 'priceRange': [],
             'RouteIds': [], 'bpKeys': [], 'dpKeys': [], 'streaksFilter': [],
             'preRouteFilters': None}

session = requests.Session()
session.cookies.update(cookies)
session.headers.update(headers)
session.get('https://www.redbus.in', timeout=10)
r = session.post('https://www.redbus.in/rpw/api/searchResults', params=params, json=json_data, timeout=15)
buses = r.json()['data']['inventories']

# Show fareDetailsBySeatType for first 3 buses
for bus in buses[:3]:
    print(f"Operator: {bus['travelsName']}")
    print(f"Bus Type: {bus['busType']}")
    print(f"fareList: {bus.get('fareList')}")
    print(f"fareDetailsBySeatType: {json.dumps(bus.get('fareDetailsBySeatType'), indent=2)}")
    print("-" * 60)
