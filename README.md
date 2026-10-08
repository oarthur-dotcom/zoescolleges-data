# Zoe's Colleges — data

This repo is the data stream for zoescolleges.com. The site reads `colleges.json` from the jsDelivr CDN, so updating this file updates the site **without a Netlify deploy**.

## How it works
1. New college data lands (a structured dataset drop, or official College Scorecard pulls).
2. The data is validated against official federal sources and a before/after diff is prepared.
3. **The owner approves the diff** (nothing ships without this).
4. The approved `colleges.json` is committed here.
5. The site picks it up from the CDN within ~minutes:
   `https://cdn.jsdelivr.net/gh/oarthur-dotcom/zoescolleges-data@main/colleges.json`
   (cache can be purged at `https://purge.jsdelivr.net/gh/oarthur-dotcom/zoescolleges-data@main/colleges.json`)

## Files
- `colleges.json` — the live dataset (schema below)
- `schema.md` — field definitions

## colleges.json schema (v1)
```json
{
  "version": 1,
  "updated": "YYYY-MM-DD",
  "source": "U.S. Dept. of Education College Scorecard + curated scene data",
  "colleges": [
    {
      "id": "unitid-or-slug",
      "name": "", "city": "", "state": "",
      "scorecard": { "admissionRate": null, "satAvg": null, "costAvg": null, "medianEarnings10yr": null, "gradRate": null, "size": null },
      "scene": { "music": [], "art": [], "sports": [], "libraries": [], "notes": "" }
    }
  ]
}
```
