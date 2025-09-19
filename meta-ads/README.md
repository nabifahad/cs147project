### Meta (Facebook & Instagram) Ads: Quick Launch Kit

This folder contains a ready-to-use plan, copy/design templates, and a minimal Python script to create a paused Campaign → Ad Set → Ads via the Meta Graph API once you add your credentials.

—

### What’s Included
- `campaign_plan.md`: Strategy, structure, KPIs, and testing plan
- `templates.md`: Ad copy templates, carousel framework, UGC prompts
- `assets_briefs.md`: Three creative briefs with specs
- `meta_ads_launch.py`: Minimal API script to create entities (paused)
- `.env.example`: Environment variables you need to supply
- `config.sample.json`: Audience and naming defaults
- `requirements.txt`: Python dependencies

—

### Prerequisites
- Meta developer app with Marketing API access approved
- System user or long-lived access token with ads_management permissions
- Ad Account ID (format: `act_XXXXXXXXX`), Page ID, Pixel ID, Business ID
- Verified domain and Pixel installed (Conversions API recommended)

—

### Setup
1) Copy env and fill values
```bash
cp .env.example .env
# Edit .env with your values
```

2) (Optional) Edit config
```bash
cp config.sample.json config.json
# Adjust names, geo, age, utms, optimization_event
```

3) Install dependencies
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

—

### Create Campaign/Ad Set/Ads (Paused)
```bash
source .venv/bin/activate
python meta_ads_launch.py ./config.json
```

Outputs IDs of created entities. All are PAUSED by default for review.

—

### Notes & Next Steps
- Replace placeholder creative with real assets: upload images/videos and reference `image_hash`/`video_id` in creative.
- For Advantage+ placements, minimal targeting is recommended; for brand constraints, add placements targeting.
- Start with small budgets, then scale winners 20–30% every 2–3 days.
- Observe policy compliance; avoid personal attributes and restricted categories.

—

### Troubleshooting
- 400/403 errors: check token scopes, business permissions, and entity ownership.
- Invalid parameter: ensure IDs are correct and domain is verified.
- Date/time: provide ISO times with timezone (e.g., `2025-09-14T18:00:00Z`).

