import logging
import time
from datetime import datetime, timedelta
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pandas as pd
from playwright.sync_api import sync_playwright, Browser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("redbus_scraper")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def _build_search_url(from_city, from_id, from_type, to_city, to_id, to_type, target_date):
    return (
        f"https://www.redbus.in/bus-tickets/{from_city.lower()}-to-{to_city.lower()}?"
        f"fromCityName={from_city}&fromCityId={from_id}&fromCityType={from_type}&"
        f"toCityName={to_city}&toCityId={to_id}&toCityType={to_type}&"
        f"onward={target_date}&doj={target_date}&ref=home"
    )


INVENTORY_KEYS = ("inv", "inventories")


def _find_inventory(payload):
    """
    Locate the bus inventory list inside the API response, regardless of whether
    it's at the top level or nested under an envelope like {"data": {...}}, and
    regardless of whether the key is named "inv" or "inventories" (RedBus has
    used both across API versions).
    Returns (inventory_list, path_used) so callers can log where it was found.
    """
    if not isinstance(payload, dict):
        return None, None

    # Direct hit at this level.
    for key in INVENTORY_KEYS:
        if isinstance(payload.get(key), list):
            return payload[key], key

    # Common envelope: {"success", "data": {...}, "statusCode", "headers"}
    inner = payload.get("data")
    if isinstance(inner, dict):
        for key in INVENTORY_KEYS:
            if isinstance(inner.get(key), list):
                return inner[key], f"data.{key}"
        # Some variants nest one level deeper, e.g. data.result.inventories
        for key, val in inner.items():
            if isinstance(val, dict):
                for inv_key in INVENTORY_KEYS:
                    if isinstance(val.get(inv_key), list):
                        return val[inv_key], f"data.{key}.{inv_key}"

    return None, None


def _extract_min_fare(bus, prefer_discounted=True):
    """
    Return the lowest fare for this bus, based on RedBus's current schema:

    1. fareDetailsBySeatType: {"SLEEPER": [{"originalPrice":.., "discountedPrice":.., "count":..}], ...}
       -- the richest source; each seat type can have its own price.
    2. fareList: flat list of numeric fares, e.g. [831.39, 942.39, ...] -- fallback.
    3. A handful of legacy/scalar keys, in case older API variants show up again.

    `prefer_discounted`: if True (default), uses discountedPrice when a live promo
    applies -- i.e. "what a customer would pay right now". Set to False to track
    originalPrice instead, if you want fare trends free of promotional noise.
    """
    def as_positive_float(v):
        try:
            f = float(v)
            return f if f > 0 else None
        except (TypeError, ValueError):
            return None

    # 1. Per-seat-type breakdown (current schema).
    fdst = bus.get("fareDetailsBySeatType")
    if isinstance(fdst, dict) and fdst:
        vals = []
        for entries in fdst.values():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                price = None
                if prefer_discounted:
                    price = as_positive_float(entry.get("discountedPrice"))
                if price is None:
                    price = as_positive_float(entry.get("originalPrice"))
                if price is not None:
                    vals.append(price)
        if vals:
            return min(vals)

    # 2. Flat fareList (current schema fallback).
    fare_list = bus.get("fareList")
    if isinstance(fare_list, list) and fare_list:
        vals = [as_positive_float(f) for f in fare_list]
        vals = [v for v in vals if v is not None]
        if vals:
            return min(vals)

    # 3. Legacy nested fareDetails list, in case older API variants reappear.
    fare_details = bus.get("fareDetails")
    if isinstance(fare_details, list) and fare_details:
        vals = [as_positive_float(f.get("totalFare") if isinstance(f, dict) else f) for f in fare_details]
        vals = [v for v in vals if v is not None]
        if vals:
            return min(vals)

    # 4. Direct scalar keys, lowest priority since they've never actually matched.
    for key in ("minFare", "totalFare", "fare", "price"):
        val = as_positive_float(bus.get(key))
        if val is not None:
            return val

    return None


def _extract_rating(bus):
    """Return this bus's rating, or None if genuinely unrated (not 0.0)."""
    for key in ("totalRatings", "avgRating", "rating", "starRating", "operatorRating"):
        try:
            r = float(bus.get(key))
            if r > 0:
                return r
        except (TypeError, ValueError):
            continue
    return None


def _parse_inventory(data, from_id, to_id, target_date):
    inventory, path_used = _find_inventory(data)

    if inventory is None:
        top_keys = list(data.keys()) if isinstance(data, dict) else type(data)
        nested_keys = (
            list(data.get("data").keys())
            if isinstance(data, dict) and isinstance(data.get("data"), dict)
            else None
        )
        logger.warning(
            "Could not locate inventory in response. Top-level keys: %s | data keys: %s",
            top_keys, nested_keys,
        )
        return []

    logger.info("Found inventory at '%s' (%d buses)", path_used, len(inventory))
    fetch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    records = []
    missing_fare_count = 0

    for i, bus in enumerate(inventory):
        fare = _extract_min_fare(bus)
        if fare is None:
            missing_fare_count += 1
        records.append({
            "fetch_timestamp": fetch_time,
            "from_city_id": from_id,
            "to_city_id": to_id,
            "journey_date": target_date,
            "operator_name": bus.get("travelsName") or bus.get("operatorName"),
            "bus_type": bus.get("busType"),
            "departure_time": bus.get("dpTime") or bus.get("departureTime"),
            "arrival_time": bus.get("arrTime") or bus.get("arrivalTime"),
            "available_seats": bus.get("availableSeats") or bus.get("seatsAvailable"),
            "price_inr": fare,
            "rating": _extract_rating(bus),
        })

    # Self-diagnosing fallback: if we couldn't find a fare for ANY bus, none of
    # our known keys matched this response's schema. Dump the raw keys/values
    # of the first bus so the real field name can be identified in one shot,
    # instead of guessing key names blind again.
    if inventory and missing_fare_count == len(inventory):
        sample = inventory[0]
        logger.warning(
            "Fare extraction matched 0/%d buses -- schema has likely changed again. "
            "First bus record keys: %s",
            len(inventory), list(sample.keys()) if isinstance(sample, dict) else type(sample),
        )
        logger.warning("First bus record (raw): %s", sample)

    return records


def _merge_pages(pages):
    """
    Merge multiple raw searchResults JSON payloads (one per scroll/page) into a
    single combined inventory list, de-duplicating buses by a stable identity.
    Returns (combined_inventory, first_page_metadata) -- metadata (busCounts etc.)
    only needs to come from the first page since it describes the whole route.
    """
    seen_ids = set()
    combined = []
    first_meta = None

    for page_data in pages:
        inventory, _ = _find_inventory(page_data)
        if inventory is None:
            continue

        if first_meta is None and isinstance(page_data, dict):
            inner = page_data.get("data") if isinstance(page_data.get("data"), dict) else page_data
            first_meta = {
                "busCounts": inner.get("busCounts"),
                "metaData": inner.get("metaData"),
            }

        for bus in inventory:
            # serviceId + doj + departureTime is a stable per-bus identity on RedBus;
            # fall back to the object's own identity if those fields are missing.
            bus_id = (bus.get("serviceId"), bus.get("doj"), bus.get("departureTime")) \
                if isinstance(bus, dict) else id(bus)
            if bus_id in seen_ids:
                continue
            seen_ids.add(bus_id)
            combined.append(bus)

    return combined, first_meta


def _fetch_json_in_page(page, url, method="GET", post_data=None):
    """Issue a fetch() from inside the page's own JS context, so it automatically
    carries the same cookies/session as the browser -- no need to manually copy
    auth headers."""
    return page.evaluate(
        """async ({url, method, postData}) => {
            const opts = { method, headers: { 'Content-Type': 'application/json' }, credentials: 'same-origin' };
            if (postData) opts.body = postData;
            const res = await fetch(url, opts);
            if (!res.ok) throw new Error('HTTP ' + res.status);
            return await res.json();
        }""",
        {"url": url, "method": method, "postData": post_data},
    )


def _replace_query_param(url: str, key: str, value: str) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query[key] = value
    new_query = urlencode(query)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


def _scrape_once(browser: Browser, search_url: str, timeout_ms: int = 30000,
                  page_pause_ms: int = 400):
    """
    Open a fresh context/page, load the search URL to get the first page of
    results, then directly replicate the same POST request with incrementing
    `offset` query params to pull every remaining page -- RedBus paginates via
    explicit limit/offset query params (confirmed from the captured request),
    not scroll-triggered lazy loading, so there's no need to simulate scrolling.
    """
    context = browser.new_context(
        user_agent=USER_AGENT,
        viewport={"width": 1366, "height": 768},
    )
    page = context.new_page()
    captured_pages = []
    first_request = {}

    def on_response(response):
        if "/rpw/api/searchResults" in response.url and response.status == 200:
            try:
                captured_pages.append(response.json())
                if "url" not in first_request:
                    req = response.request
                    first_request["url"] = req.url
                    first_request["method"] = req.method
                    first_request["post_data"] = req.post_data
            except Exception as e:
                logger.warning("Failed to parse a searchResults response: %s", e)

    page.on("response", on_response)

    try:
        with page.expect_response(
            lambda res: "/rpw/api/searchResults" in res.url and res.status == 200,
            timeout=timeout_ms,
        ):
            page.goto(search_url, wait_until="domcontentloaded", timeout=timeout_ms)

        if not captured_pages or "url" not in first_request:
            logger.warning("No initial searchResults response captured.")
            return {"data": {"inventories": []}}

        first_inventory, meta = _merge_pages(captured_pages)
        query = dict(parse_qsl(urlsplit(first_request["url"]).query))
        limit = int(query.get("limit", len(first_inventory) or 10))
        total = None
        if meta and isinstance(meta.get("busCounts"), dict):
            total = meta["busCounts"].get("total")
        elif meta and isinstance(meta.get("metaData"), dict):
            total = meta["metaData"].get("totalCount")

        if not total or limit <= 0:
            logger.info("No pagination total found; returning first page only (%d buses).", len(first_inventory))
        else:
            logger.info("Route has %d total buses, %d per page -- fetching remaining pages.", total, limit)
            offsets_needed = range(limit, total, limit)
            for offset in offsets_needed:
                page_url = _replace_query_param(first_request["url"], "offset", str(offset))
                try:
                    page_data = _fetch_json_in_page(
                        page, page_url, method=first_request["method"], post_data=first_request["post_data"]
                    )
                    captured_pages.append(page_data)
                    inv, _ = _find_inventory(page_data)
                    logger.info("Fetched offset=%d: %d buses", offset, len(inv) if inv else 0)
                except Exception as e:
                    logger.warning("Failed to fetch offset=%d: %s", offset, e)
                page.wait_for_timeout(page_pause_ms)  # gentle pacing between requests

        combined_inventory, meta = _merge_pages(captured_pages)
        logger.info(
            "Collected %d searchResults page(s), %d unique buses total.",
            len(captured_pages), len(combined_inventory),
        )

        _, path_used = _find_inventory(captured_pages[0])
        if path_used and path_used.startswith("data."):
            key = path_used.split(".", 1)[1]
            return {"data": {key: combined_inventory}}
        elif path_used:
            return {path_used: combined_inventory}
        else:
            return {"data": {"inventories": combined_inventory}}

    finally:
        context.close()


def scrape_bus_data(
    from_city="Coimbatore",
    from_id="141",
    from_type="CITY",
    to_city="Madurai",
    to_id="126",
    to_type="CITY",
    days_ahead=7,
    max_retries=3,
    retry_backoff_seconds=5,
    browser=None,
):
    """
    Scrape bus inventory for a single route/date from RedBus's internal search API.

    If `browser` is passed in (an already-launched Playwright Browser), it will be
    reused instead of launching a new one -- much cheaper when calling this in a loop
    over multiple routes/dates.
    """
    target_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%d-%b-%Y")
    search_url = _build_search_url(from_city, from_id, from_type, to_city, to_id, to_type, target_date)

    logger.info("Scraping route %s (%s) -> %s (%s) for %s", from_city, from_id, to_city, to_id, target_date)

    owns_browser = browser is None
    playwright_ctx = None
    records = []

    try:
        if owns_browser:
            playwright_ctx = sync_playwright().start()
            browser = playwright_ctx.chromium.launch(
                headless=True,
                channel="chrome",
                args=["--disable-blink-features=AutomationControlled"],
            )

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                data = _scrape_once(browser, search_url)
                records = _parse_inventory(data, from_id, to_id, target_date)
                logger.info("Attempt %d succeeded: %d buses extracted", attempt, len(records))
                break
            except Exception as e:
                last_error = e
                logger.warning("Attempt %d/%d failed: %s", attempt, max_retries, e)
                if attempt < max_retries:
                    time.sleep(retry_backoff_seconds * attempt)  # linear backoff
        else:
            logger.error("All %d attempts failed. Last error: %s", max_retries, last_error)

    finally:
        if owns_browser:
            if browser:
                browser.close()
            if playwright_ctx:
                playwright_ctx.stop()

    return pd.DataFrame(records)


def scrape_multiple_routes(routes, days_ahead=7, max_retries=3):
    """
    Scrape several routes reusing a single browser instance.

    routes: list of dicts, each like:
        {"from_city": "Coimbatore", "from_id": "141", "to_city": "Madurai", "to_id": "126"}
    """
    all_frames = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
        )
        try:
            for route in routes:
                df = scrape_bus_data(
                    from_city=route["from_city"],
                    from_id=route["from_id"],
                    to_city=route["to_city"],
                    to_id=route["to_id"],
                    days_ahead=days_ahead,
                    max_retries=max_retries,
                    browser=browser,
                )
                all_frames.append(df)
                time.sleep(2)  # gentle pacing between requests
        finally:
            browser.close()

    return pd.concat(all_frames, ignore_index=True) if all_frames else pd.DataFrame()


# ===================================================
# MAIN EXECUTION
# ===================================================
if __name__ == "__main__":
    df = scrape_bus_data(from_city="Coimbatore", from_id="141", to_city="Madurai", to_id="126", days_ahead=7)

    if not df.empty:
        logger.info("SUCCESS: Extracted %d records", len(df))
        print(df[["operator_name", "bus_type", "available_seats", "price_inr", "rating"]].head(10))
    else:
        logger.error("Failed to capture records.")