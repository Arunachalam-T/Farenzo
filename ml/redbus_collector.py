"""
Farenzo - RedBus Data Collector
Uses your OWN browser session cookies to query the RedBus search API.
WARNING: Cookies expire quickly (usually within 2-8 hours). 
         Refresh cookies from your browser DevTools when you get 401/403 errors.
"""

import requests
import pandas as pd
import os
import time
from datetime import datetime, timedelta

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: YOUR SESSION COOKIES (Captured from your own browser DevTools)
# These will expire! Update them from DevTools > Application > Cookies
# ─────────────────────────────────────────────────────────────────────────────
cookies = {
    'rbuuid': 'ca34d1d0-842d-11f1-8a27-831578cf5b15',
    'mriClientId': 'BRca34d1d1-842d-11f1-8a27-831578cf5b15',
    'rayHomeAB': 'V1',
    'freeSearchAB': 'V2',
    '_ga': 'GA1.1.484928212.1784546770',
    'country': 'IND',
    'currency': 'INR',
    'selectedCurrency': 'INR',
    'defaultLanguage': 'en',
    'language': 'en',
    'mriSessionId': 'BR9ff7df50-a23e-11f1-a84d-ebe8e11fb442',
    'env': 'PROD',
    'buildVersion': 'PROD_be1f247576',
    'funnelVariant': 'RESPONSIVE',
    'defaultlanguage': 'en',
    '_abck': '3C84BC9A599E13D86180BF7E4394F1FB~-1~YAAQ9cEzuHBTlzOgAQAAM5pQRBBgvip8mpQMxuHBJOK/Twu4aA/rLAXO1kYb5VwH+DSJsr7JzlfujKeZbuPH6NuKDfmNwSdB77yxgDUwzalMmWEQokUYboTv/59/S4APCGdOfEqNlCIX4YcTzsynIGFe8X4tVZfwThaulALlfXtXfH76BIUCW4pb2U5exkhPRQlRsPRtPFFrgOOM61Q1b+F04cP7/l/xlnJwHJen8ScGIN2ipxrh+/ADxuXdJoc/aM48RTWoo0O0Atj0SuPnv5aoQTXOGkvcViy0Xum7A5ViXv98Tri99oDL+/VZ/UxLzkyzR5qmF0VkO0M49QEUhM7Ahlz7h4zaE0fVMwproE4bPNKj/gf+6jcfI++rRviZHci5tiAWVN6QENO0wxSvXn7WRmQyXs7wPS5z0vK7zDIXodZJghV6E5kJDMecerVeS1pPebkiKpK2YR932EJfIx3jsaiw9/F4uLgoRrpeFBbm9iKxeQE4Kg756W9t~-1~-1~-1~-1~-1',
    '_gcl_au': '1.1.492619714.1787852534',
    'rb_fpData': '%7B%22userAgent%22%3A%22Mozilla%2F5.0%20(Windows%20NT%2010.0%3B%20Win64%3B%20x64)%20AppleWebKit%2F537.36%20(KHTML%2C%20like%20Gecko)%20Chrome%2F151.0.0.0%20Safari%2F537.36%22%2C%22browser%22%3A%22Chrome%22%2C%22version%22%3A%22151.0.0.0%22%2C%22os%22%3A%22Windows%22%2C%22osVersion%22%3A%2210.0%22%2C%22deviceType%22%3A%22Desktop%22%2C%22screenSize%22%3A%221536%2C816%22%2C%22screenDPI%22%3A1.25%2C%22screenResolution%22%3A%221920x1080%22%2C%22screenColorDepth%22%3A24%2C%22aspectRatio%22%3A%2216%3A9%22%2C%22systemLanguage%22%3A%22en-US%22%2C%22connection%22%3A%224g%22%2C%22effectiveConnection%22%3A%224g%22%2C%22timeZone%22%3A5.5%7D',
    'prev_mriSessionId': 'BR9ff7df50-a23e-11f1-a84d-ebe8e11fb442',
    'channel': 'MWEB',
    'ak_bmsc': 'B4ACA5BB9CE8910126D084EBA271A581~000000000000000000000000000000~YAAQnsEzuAkIBj+gAQAA9kFRRADotvpLgEnoLm687ea6hTNSc0ed9zyTF3MsR7Ndh6LFiZmbjBjzn47RiJkkT/ZerEPbYnOboV0gye4ws6S5p+giln1eaTxQDvdDkcZ8D8rs4GZVRK5+5M2SXG4l2r1VeXnQdiLAZZLp3HeRrdUrucmXfMGAjYqImhpa62gOGgVikqBKW2lgKxEHsfFkbmg3UOwwa84JPqgswnW+ifdYLWjQhUUcrsq2YlynIlcb3J3LL/oePepVJx2W6RJ+o1c1uWtY356YldGy45PhTa2wRAj5pxyomSeosIqD4mBfYSqCVzfACANhlGX5JqgN45FqpDHtfa27ncNagk+Hp4d7ZTzRG+//jFpQcMNdh6ckNo9h5vvQABBdL4EKCFs6r/tgmbrnpoAqiTUrbKJn++i0HEs0ewaNJuP5XddnxgrMk4Ti7HfYxfiuY38JTxx54Nr3GpunjYpa66563UlVK17HRiQrQ+/SbFSVQujAnw==',
    'bm_sz': '32D2751E7E9FE86DBE8AA16BB9513958~YAAQjkU5Fy+vnUKgAQAAUSlSRAB4fLDX8UCwSH4pSvi/23VcEAa2tLViJFlufX3IsZRZtOUST/y9KiYLynNHUyxQSQNEHqvlm7pCHHG1FooUSdJdT9Wu52Ap1bhYhNLQXYKxYnBao9dUmIrjoSPqQhbMsO8xU6JIcDkC1jk+CEK1Tx14+6ItSZqrWVNwQjo7mEP7v5ZfE67maWg2tNtSk3rjHZWE4U8ultbSB6Lx6qUzgTfWFStzqVu13X79o0T8MT8+rz3C5lMc1K8G+P5C8uGEujeQk7VcgMeiGrdAoyoEe9FnJtRs2KoieF+XYHS92FxtuW7l7c8ukBLqJFv7uSm9ZCf+vYV0eIgH8SYJLLWJw/rPRdIayl60EldNp9YNL29KkEp+wJtQQjn9WD+ez3Yc77GMlu9snSF+cDnzuj8chcZn8ORtxxFX9jm5z7E8d8ER4g==~3752772~3753013',
    'bm_sv': '9AAEE3D2F09B6D455649A96CF2AE8177~YAAQjkU5F1WvnUKgAQAADixSRAC3xXvRI3Titx0xXZ7L3G6dohk1L9B8CSN0qQn8lE2jL1+L93fAACJqQgsI6l2ZGdrHBsnH8D4M7HZW/v4zmPD59p1KLSJw1zcVvMIEgL4ptvJnFFXmJH1SPpPuoq00AUbDgZC1HewV7uENG1/FnQb0q0dAOLmxT3zs/oCPD0BNWqrVNK+w88LSOaP8dkRbfBX5WsHlWruY9+oDYy+qKssUdtfp0Mpb09Q26DgC~1',
    '_ga_W2P7QGN8S2': 'GS2.1.s1787852533$o3$g1$t1787852634$j41$l0$h1642738879',
    'rayBetaAB': 'V2',
    'aiSmartFilterUIAB': 'V0',
    'geolocationAB': 'V0',
    'leanerFunnelAB': 'V2',
    'paymentBackAB': 'V3',
    'unifiedSrpTabsABNew': 'V2',
    'retainAddonsAB': 'V2',
    'srpInlineOfferAB': 'V3',
    'abExpsVariantsForMri': '["rayBetaAB:V2","aiSmartFilterUIAB:V0","geolocationAB:V0","leanerFunnelAB:V2","paymentBackAB:V3","retainAddonsAB:V2","srpInlineOfferAB:V3"]',
}

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: BROWSER HEADERS (Mimics a Mobile Chrome browser)
# ─────────────────────────────────────────────────────────────────────────────
headers = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/json',
    'origin': 'https://www.redbus.in',
    'priority': 'u=1, i',
    'sec-ch-ua': '"Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Mobile Safari/537.36',
}

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: ROUTE CONFIGURATION
# City IDs found from redbus.in URL when searching routes
# ─────────────────────────────────────────────────────────────────────────────
ROUTES = [
    {'from': '141', 'to': '126', 'name': 'Coimbatore to Madurai'},
    {'from': '126', 'to': '141', 'name': 'Madurai to Coimbatore'},
    {'from': '126', 'to': '123', 'name': 'Madurai to Chennai'},
    {'from': '123', 'to': '126', 'name': 'Chennai to Madurai'},
    {'from': '141', 'to': '123', 'name': 'Coimbatore to Chennai'},
    {'from': '123', 'to': '141', 'name': 'Chennai to Coimbatore'},
]

OUTPUT_CSV = 'redbus_fares.csv'


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: CORE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def build_params(from_city, to_city, days_ahead=1):
    """Build query parameters for a given route and date."""
    target_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%d-%b-%Y')
    return {
        'fromCity': str(from_city),
        'toCity': str(to_city),
        'DOJ': target_date,
        'limit': '50',
        'offset': '0',
        'meta': 'true',
        'groupId': '0',
        'sectionId': '0',
        'sort': '0',
        'sortOrder': '0',
        'from': 'initialLoad',
        'getUuid': 'true',
        'bT': '1',
        'clearLMBFilter': 'undefined',
        'isFilterApplied': 'false',
    }


def build_json_body():
    """Empty filter body required by the API."""
    return {
        'appliedFilterCount': 0,
        'onlyShow': [], 'dt': [], 'SeaterType': [], 'AcType': [],
        'travelsList': [], 'amtList': [], 'bpList': [], 'dpList': [],
        'CampaignFilter': [], 'at': [], 'persuasionList': [],
        'bpIdentifier': [], 'dpIdentifier': [], 'bcf': [],
        'opBusTypeFilterList': [], 'priceRange': [], 'RouteIds': [],
        'bpKeys': [], 'dpKeys': [], 'streaksFilter': [],
        'preRouteFilters': None,
    }


def parse_buses(data, params):
    """Extract bus records from the API JSON response."""
    inner = data.get('data', {})
    bus_list = inner.get('inventories', [])
    records = []
    for bus in bus_list:
        # fareDetailsBySeatType gives per-seat-type pricing with original + discounted
        fare_by_type = bus.get('fareDetailsBySeatType', {})

        # Extract prices per seat type
        seater_fare     = fare_by_type.get('SEATER', [{}])[0].get('originalPrice') if fare_by_type.get('SEATER') else None
        seater_discount = fare_by_type.get('SEATER', [{}])[0].get('discountedPrice') if fare_by_type.get('SEATER') else None
        sleeper_fare    = fare_by_type.get('SLEEPER', [{}])[0].get('originalPrice') if fare_by_type.get('SLEEPER') else None
        sleeper_discount= fare_by_type.get('SLEEPER', [{}])[0].get('discountedPrice') if fare_by_type.get('SLEEPER') else None
        single_sl_fare  = fare_by_type.get('SINGLE_SLEEPER', [{}])[0].get('originalPrice') if fare_by_type.get('SINGLE_SLEEPER') else None

        # Min fare across all types (for comparison)
        fare_list = bus.get('fareList', [])
        min_fare = min(fare_list) if fare_list else None

        records.append({
            'query_timestamp':   datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'from_city_id':      params.get('fromCity'),
            'from_city':         inner.get('parentSrcCityName', ''),
            'to_city_id':        params.get('toCity'),
            'to_city':           inner.get('parentDstCityName', ''),
            'journey_date':      params.get('DOJ'),
            'operator_id':       bus.get('operatorId'),
            'operator_name':     bus.get('travelsName'),
            'bus_type':          bus.get('busType'),
            'is_ac':             bus.get('isAc'),
            'is_sleeper':        bus.get('isSleeper'),
            'departure_time':    bus.get('departureTime'),
            'arrival_time':      bus.get('arrivalTime'),
            'duration_mins':     bus.get('journeyDurationMin'),
            'available_seats':   bus.get('availableSeats'),
            'total_seats':       bus.get('totalSeats'),
            # Overall min fare
            'min_fare_inr':      min_fare,
            # Per seat type fares (the important part!)
            'seater_fare':       seater_fare,
            'seater_discounted': seater_discount,
            'sleeper_fare':      sleeper_fare,
            'sleeper_discounted':sleeper_discount,
            'single_sleeper_fare': single_sl_fare,
            # Ratings
            'bus_score':         bus.get('busScore'),
            'total_ratings':     bus.get('totalRatings'),
        })
    return records



def fetch_route(from_city, to_city, days_ahead=1):
    """Hit the RedBus search API for a single route and date."""
    params = build_params(from_city, to_city, days_ahead)
    session = requests.Session()
    session.cookies.update(cookies)
    session.headers.update(headers)
    # Prime the session first (helps with cookie-based auth)
    session.get('https://www.redbus.in', timeout=10)

    response = session.post(
        'https://www.redbus.in/rpw/api/searchResults',
        params=params,
        json=build_json_body(),
        timeout=15
    )

    if response.status_code == 200:
        data = response.json()
        records = parse_buses(data, params)
        print(f"  [OK] Got {len(records)} buses for {params['DOJ']}")
        return records
    else:
        print(f"  [FAIL] HTTP {response.status_code} -- Cookies may have expired!")
        print(f"     Response: {response.text[:200]}")
        return []


def save_to_csv(records):
    """Append records to CSV (creates file if not exists)."""
    if not records:
        return
    df = pd.DataFrame(records)
    file_exists = os.path.exists(OUTPUT_CSV)
    df.to_csv(OUTPUT_CSV, mode='a', header=not file_exists, index=False)
    print(f"  [SAVED] {len(records)} records to {OUTPUT_CSV}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: MAIN - Run a collection sweep across all routes & upcoming dates
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # Collect for ALL days from tomorrow up to 30 days ahead (next month)
    # Each run captures prices at that MOMENT - run every 4 hours for price tracking
    DAYS_TO_COLLECT = list(range(1, 31))  # Day 1 to Day 30

    all_records = []
    total_routes = len(ROUTES)

    for i, route in enumerate(ROUTES, 1):
        print(f"\n[{i}/{total_routes}] Route: {route['name']}")
        for days in DAYS_TO_COLLECT:
            records = fetch_route(route['from'], route['to'], days_ahead=days)
            all_records.extend(records)
            if records:
                time.sleep(1.5)  # 1.5s delay between requests

    save_to_csv(all_records)

    # Summary
    if all_records:
        df_new = pd.DataFrame(all_records)
        print(f"\n[DONE] Collected {len(all_records)} new records this run")
        if os.path.exists(OUTPUT_CSV):
            df_total = pd.read_csv(OUTPUT_CSV)
            print(f"[TOTAL] CSV now has {len(df_total)} records total")
        print(f"[FILE] Saved to: {os.path.abspath(OUTPUT_CSV)}")
        print(f"\n[PRICE SAMPLE] Min fares captured:")
        summary = df_new.groupby(['from_city','to_city','journey_date'])['min_fare_inr'].min().reset_index()
        print(summary.to_string(index=False))
    else:
        print("[WARN] No records collected - cookies may have expired!")
        print("       Go to redbus.in in Chrome, open DevTools > Application > Cookies")
        print("       Copy fresh cookies into this script and try again.")
