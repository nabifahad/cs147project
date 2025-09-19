#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

import requests
from dotenv import load_dotenv


API_BASE = "https://graph.facebook.com/v20.0"


def require_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise RuntimeError(f"Missing environment variable: {var_name}")
    return value


def read_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_url_with_utms(base_url: str, utm_params: dict) -> str:
    if not utm_params:
        return base_url
    parsed = urlparse(base_url)
    query = dict(parse_qsl(parsed.query))
    # Replace token with a real value later per ad
    for k, v in utm_params.items():
        query[k] = v
    new_query = urlencode(query)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))


def fb_post(path: str, token: str, payload: dict) -> dict:
    url = f"{API_BASE}/{path}"
    data = {**payload, "access_token": token}
    resp = requests.post(url, data=data, timeout=60)
    if not resp.ok:
        raise RuntimeError(f"POST {url} failed: {resp.status_code} {resp.text}")
    return resp.json()


def create_campaign(ad_account_id: str, token: str, name: str, objective: str, spend_cap_cents: int | None = None) -> str:
    payload = {
        "name": name,
        "objective": objective,  # E.g., SALES, LEAD_GENERATION
        "status": "PAUSED",
        "special_ad_categories": [],
        "buying_type": "AUCTION",
    }
    if spend_cap_cents is not None:
        payload["spend_cap"] = spend_cap_cents
    resp = fb_post(f"{ad_account_id}/campaigns", token, payload)
    return resp["id"]


def create_adset(ad_account_id: str, token: str, name: str, campaign_id: str, pixel_id: str, optimization_event: str, daily_budget_cents: int, countries: list[str], age_min: int | None, age_max: int | None, genders: list[int] | None, start_time_iso: str | None, end_time_iso: str | None) -> str:
    now = datetime.now(timezone.utc) + timedelta(minutes=10)
    start_time = start_time_iso or now.isoformat()
    payload = {
        "name": name,
        "campaign_id": campaign_id,
        "status": "PAUSED",
        "daily_budget": daily_budget_cents,
        "billing_event": "IMPRESSIONS",
        "optimization_goal": optimization_event,  # e.g., PURCHASE, LEAD
        "destination_type": "WEBSITE",
        "promoted_object": json.dumps({"pixel_id": pixel_id, "custom_event_type": optimization_event}),
        "start_time": start_time,
        "targeting": json.dumps({
            "geo_locations": {"countries": countries},
            "age_min": age_min or 18,
            "age_max": age_max or 65,
            # genders: 1 male, 2 female; empty means all
            **({"genders": genders} if genders else {}),
            # Advantage+ placements when omitted; keep minimal targeting
        }),
    }
    if end_time_iso:
        payload["end_time"] = end_time_iso
    resp = fb_post(f"{ad_account_id}/adsets", token, payload)
    return resp["id"]


def create_creative_from_url(token: str, ad_account_id: str, page_id: str, name: str, message: str, headline: str, link_url: str) -> str:
    payload = {
        "name": name,
        "object_story_spec": json.dumps({
            "page_id": page_id,
            "link_data": {
                "message": message,
                "link": link_url,
                "name": headline,
                # Add image_hash or media when available
            },
        })
    }
    resp = fb_post(f"{ad_account_id}/adcreatives", token, payload)
    return resp["id"]


def create_ad(token: str, ad_account_id: str, adset_id: str, name: str, creative_id: str) -> str:
    payload = {
        "name": name,
        "adset_id": adset_id,
        "creative": json.dumps({"creative_id": creative_id}),
        "status": "PAUSED",
        # Limit to ensure review before running
    }
    resp = fb_post(f"{ad_account_id}/ads", token, payload)
    return resp["id"]


def main():
    load_dotenv()
    access_token = require_env("META_ACCESS_TOKEN")
    ad_account_id = require_env("META_AD_ACCOUNT_ID")
    page_id = require_env("META_PAGE_ID")
    pixel_id = require_env("META_PIXEL_ID")
    website_url = require_env("WEBSITE_URL")
    daily_budget_cents = int(require_env("DAILY_BUDGET_CENTS"))

    config_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "config.sample.json")
    cfg = read_config(config_path)

    campaign_objective = os.getenv("CAMPAIGN_OBJECTIVE", "SALES")
    campaign_id = create_campaign(ad_account_id, access_token, cfg["campaign_name"], campaign_objective)
    print(f"Created Campaign: {campaign_id}")

    adset_id = create_adset(
        ad_account_id=ad_account_id,
        token=access_token,
        name=cfg["adset_name"],
        campaign_id=campaign_id,
        pixel_id=pixel_id,
        optimization_event=cfg.get("optimization_event", "PURCHASE"),
        daily_budget_cents=daily_budget_cents,
        countries=cfg.get("countries", [os.getenv("TARGET_COUNTRY", "US")]),
        age_min=cfg.get("age_min"),
        age_max=cfg.get("age_max"),
        genders=cfg.get("genders"),
        start_time_iso=cfg.get("start_time_iso") or None,
        end_time_iso=cfg.get("end_time_iso") or None,
    )
    print(f"Created Ad Set: {adset_id}")

    headline = "Try It Risk-Free"
    message = "Get [Product] today with fast shipping and easy returns."
    base_url = website_url
    # First creative as example; you can duplicate for others
    link_with_utms = build_url_with_utms(base_url, cfg.get("utm_params", {}))
    creative_id = create_creative_from_url(
        token=access_token,
        ad_account_id=ad_account_id,
        page_id=page_id,
        name="Default Link Ad",
        message=message,
        headline=headline,
        link_url=link_with_utms,
    )
    print(f"Created Ad Creative: {creative_id}")

    # Create simple ads per names
    for ad_name in cfg.get("ad_names", ["Primary Ad"]):
        # Replace token in utm_content
        utms = cfg.get("utm_params", {}).copy()
        if "utm_content" in utms:
            utms["utm_content"] = utms["utm_content"].replace("{{ad.name}}", ad_name)
        ad_link = build_url_with_utms(base_url, utms)
        # Reuse creative or create unique per ad if needed
        creative_id_for_ad = creative_id

        ad_id = create_ad(
            token=access_token,
            ad_account_id=ad_account_id,
            adset_id=adset_id,
            name=ad_name,
            creative_id=creative_id_for_ad,
        )
        print(f"Created Ad: {ad_id} ({ad_name})")

    print("All entities created in PAUSED state. Review in Ads Manager before turning on.")


if __name__ == "__main__":
    main()

