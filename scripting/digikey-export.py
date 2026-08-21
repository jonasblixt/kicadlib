#!/usr/bin/env python3
"""
digikey_export.py
==================

Export electronic components from the DigiKey Product Information API (v4)
to a CSV file, with optional filtering by manufacturer and/or series.

Every field DigiKey returns for a product is included in the CSV (nested
objects are flattened into dotted columns, e.g. "Manufacturer.Name"; the
per-part parametric attributes -- resistance, tolerance, package, etc. --
each become their own "Parameter: <name>" column). Column set is derived
from whatever the API actually returns, so it can vary a bit by category.

SETUP
-----
1. Create an app at https://developer.digikey.com (Organization -> create an
   app). You need the "Product Information V4" API enabled. Copy the
   Client ID and Client Secret it gives you.

2. Install dependencies:
       pip install requests python-dotenv --break-system-packages

3. Provide credentials -- any of these work:
     - CLI flags:            --client-id ... --client-secret ...
     - Environment variables: DIGIKEY_CLIENT_ID / DIGIKEY_CLIENT_SECRET
     - A `.env` file next to this script:
           DIGIKEY_CLIENT_ID=xxxxxxxx
           DIGIKEY_CLIENT_SECRET=xxxxxxxx

   This script uses DigiKey's 2-legged (client_credentials) OAuth flow, so
   no browser login step is needed.

USAGE
-----
    # All Microchip parts in the ATmega series
    python digikey_export.py --manufacturer "Microchip" --series "ATmega" -o atmega_parts.csv

    # Just by series
    python digikey_export.py --series "ATmega" -o atmega_parts.csv

    # Try it against DigiKey's sandbox (dummy data) first
    python digikey_export.py --manufacturer "Microchip" --sandbox -o test.csv

    # Pass credentials on the command line instead of env vars
    python digikey_export.py --manufacturer "Microchip" --client-id XXX --client-secret YYY

NOTES ON FILTERING
-------------------
DigiKey's underlying search endpoint (KeywordSearch) always requires some
search text, and can filter server-side by manufacturer/series *ID* -- but
those IDs aren't generally known up front and looking them up is a separate
API call. So this script builds its search text from whatever you pass to
--manufacturer / --series, then re-checks every result with a case-insensitive
substring match against the actual Manufacturer/Series fields, so the CSV only
ever contains genuine matches regardless of what the search itself turned up.
At least one of --manufacturer / --series is required.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Iterable, Optional

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional; env vars can be set another way


# --------------------------------------------------------------------------
# API endpoints
# --------------------------------------------------------------------------

PROD_HOST = "https://api.digikey.com"
SANDBOX_HOST = "https://sandbox-api.digikey.com"

TOKEN_PATH = "/v1/oauth2/token"
KEYWORD_SEARCH_PATH = "/products/v4/search/keyword"


# --------------------------------------------------------------------------
# Defensive lookups used only for the --manufacturer / --series filters.
# DigiKey nests these fields as {"Id": ..., "Name"/"Value": ...} objects in
# some responses and as plain strings in others -- try both.
# --------------------------------------------------------------------------

def _first(d: dict, *keys: str) -> Any:
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


def _nested_name(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return _first(value, "Name", "Value", "Text") or (
            str(value.get("Id")) if value.get("Id") is not None else None
        )
    return str(value)


def get_manufacturer(p: dict) -> Optional[str]:
    return _nested_name(_first(p, "Manufacturer", "ManufacturerName"))


def get_series(p: dict) -> Optional[str]:
    return _nested_name(_first(p, "Series", "SeriesName"))


# --------------------------------------------------------------------------
# Flatten a raw product record into a single-level dict for CSV output.
# --------------------------------------------------------------------------

def _param_name(param: dict) -> Optional[str]:
    return _first(param, "ParameterText", "Parameter", "ParameterName", "Name")


def _param_value(param: dict) -> Optional[str]:
    return _first(param, "ValueText", "Value", "ParameterValue")


def flatten_product(obj: Any, prefix: str = "") -> dict:
    """Recursively flatten a product dict into {dotted.key: scalar}.

    Special-cases the "Parameters" list (per-part parametric attributes like
    Resistance, Tolerance, Package) into one "Parameter: <name>" column per
    attribute, since that's far more useful than "Parameters.0.Value" columns
    that don't line up across different products/categories.
    """
    flat: dict = {}
    if not isinstance(obj, dict):
        return flat

    for key, value in obj.items():
        flat_key = f"{prefix}.{key}" if prefix else key

        if key == "Parameters" and isinstance(value, list):
            for param in value:
                if isinstance(param, dict):
                    pname = _param_name(param)
                    pval = _param_value(param)
                    if pname:
                        flat[f"Parameter: {pname}"] = pval
                        continue
                # Fall back to a generic dump if we don't recognize the shape
                flat.setdefault(flat_key, []).append(param)
            if isinstance(flat.get(flat_key), list):
                flat[flat_key] = json.dumps(flat[flat_key], ensure_ascii=False)
            continue

        if isinstance(value, dict):
            flat.update(flatten_product(value, flat_key))
        elif isinstance(value, list):
            if all(isinstance(v, (str, int, float, bool)) or v is None for v in value):
                flat[flat_key] = "; ".join("" if v is None else str(v) for v in value)
            else:
                flat[flat_key] = json.dumps(value, ensure_ascii=False)
        else:
            flat[flat_key] = value

    return flat


# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------

class DigiKeyAuth:
    def __init__(self, client_id: str, client_secret: str, host: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.host = host
        self._token: Optional[str] = None
        self._expires_at: Optional[datetime] = None

    def get_token(self) -> str:
        if self._token and self._expires_at and datetime.utcnow() < self._expires_at:
            return self._token

        resp = requests.post(
            f"{self.host}{TOKEN_PATH}",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            },
            timeout=30,
        )
        if not resp.ok:
            raise RuntimeError(
                f"Failed to get DigiKey access token ({resp.status_code}): {resp.text}"
            )
        payload = resp.json()
        self._token = payload["access_token"]
        expires_in = int(payload.get("expires_in", 600))
        # Refresh a bit early to avoid using a token that expires mid-request.
        self._expires_at = datetime.utcnow() + timedelta(seconds=max(expires_in - 30, 30))
        return self._token


# --------------------------------------------------------------------------
# API client
# --------------------------------------------------------------------------

class DigiKeyClient:
    def __init__(
        self,
        auth: DigiKeyAuth,
        host: str,
        client_id: str,
        locale_site: str = "US",
        locale_language: str = "en",
        locale_currency: str = "USD",
    ):
        self.auth = auth
        self.host = host
        self.client_id = client_id
        self.locale_site = locale_site
        self.locale_language = locale_language
        self.locale_currency = locale_currency

    def _headers(self) -> dict:
        return {
            "X-DIGIKEY-Client-Id": self.client_id,
            "Authorization": f"Bearer {self.auth.get_token()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-DIGIKEY-Locale-Site": self.locale_site,
            "X-DIGIKEY-Locale-Language": self.locale_language,
            "X-DIGIKEY-Locale-Currency": self.locale_currency,
        }

    def keyword_search(
        self,
        keywords: str,
        limit: int,
        offset: int,
        max_retries: int = 5,
    ) -> dict:
        body = {"Keywords": keywords, "Limit": limit, "Offset": offset}

        url = f"{self.host}{KEYWORD_SEARCH_PATH}"
        backoff = 1.0
        last_error = None

        for attempt in range(1, max_retries + 1):
            resp = requests.post(url, headers=self._headers(), data=json.dumps(body), timeout=30)

            if resp.ok:
                return resp.json()

            if resp.status_code == 429 or resp.status_code >= 500:
                retry_after = resp.headers.get("Retry-After")
                wait = float(retry_after) if retry_after else backoff
                last_error = f"{resp.status_code}: {resp.text}"
                time.sleep(wait)
                backoff = min(backoff * 2, 30)
                continue

            # 4xx (other than 429) won't be fixed by retrying.
            raise RuntimeError(
                f"DigiKey search failed ({resp.status_code}) for body={body}: {resp.text}"
            )

        raise RuntimeError(f"DigiKey search failed after {max_retries} retries: {last_error}")


# --------------------------------------------------------------------------
# Filtering + export
# --------------------------------------------------------------------------

def matches(value: Optional[str], needle: Optional[str]) -> bool:
    if not needle:
        return True
    if not value:
        return False
    return needle.strip().lower() in value.strip().lower()


def iter_filtered_products(
    client: DigiKeyClient,
    keywords: str,
    manufacturer: Optional[str],
    series: Optional[str],
    page_size: int,
    max_pages: int,
    verbose: bool,
) -> Iterable[dict]:
    offset = 0
    for page in range(max_pages):
        data = client.keyword_search(keywords=keywords, limit=page_size, offset=offset)
        products = data.get("Products")
        if products is None and isinstance(data, list):
            products = data
        products = products or []

        if verbose:
            print(f"[page {page}] offset={offset} fetched={len(products)}", file=sys.stderr)

        if not products:
            break

        for p in products:
            m = get_manufacturer(p)
            s = get_series(p)
            if matches(m, manufacturer) and matches(s, series):
                yield p

        if len(products) < page_size:
            break
        offset += page_size


def write_csv(rows: list[dict], output_path: str) -> int:
    # Column order: first-seen order across all rows, so common fields
    # (which tend to appear first in every product) stay near the front.
    fieldnames: list[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", restval="")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return len(rows)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export DigiKey product search results to CSV, with manufacturer/series filtering.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--manufacturer", help="Case-insensitive substring match against the result's manufacturer name.")
    parser.add_argument("--series", help="Case-insensitive substring match against the result's series name.")
    parser.add_argument("--client-id", default=None, help="DigiKey app Client ID. Falls back to the DIGIKEY_CLIENT_ID env var.")
    parser.add_argument("--client-secret", default=None, help="DigiKey app Client Secret. Falls back to the DIGIKEY_CLIENT_SECRET env var.")
    parser.add_argument("-o", "--output", default=None, help="Output CSV path (default: derived from --manufacturer/--series).")
    parser.add_argument("--max-results", type=int, default=None, help="Stop after this many matching rows.")
    parser.add_argument("--page-size", type=int, default=50, help="Results per API request (DigiKey max is typically 50). Default 50.")
    parser.add_argument("--max-pages", type=int, default=200, help="Safety cap on number of pages fetched. Default 200.")
    parser.add_argument("--sandbox", action="store_true", help="Use DigiKey's sandbox API (dummy data) instead of production.")
    parser.add_argument("--locale-site", default="US")
    parser.add_argument("--locale-language", default="en")
    parser.add_argument("--locale-currency", default="USD")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print progress to stderr.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)

    client_id = args.client_id or os.environ.get("DIGIKEY_CLIENT_ID")
    client_secret = args.client_secret or os.environ.get("DIGIKEY_CLIENT_SECRET")
    if not client_id or not client_secret:
        print(
            "ERROR: Provide DigiKey credentials via --client-id/--client-secret, "
            "or DIGIKEY_CLIENT_ID/DIGIKEY_CLIENT_SECRET (env vars or a .env file).",
            file=sys.stderr,
        )
        return 1

    if not args.manufacturer and not args.series:
        print("ERROR: Provide at least one of --manufacturer or --series to search on.", file=sys.stderr)
        return 1

    # DigiKey's search endpoint always needs some search text; build it from
    # whatever filters were given. Results are still re-checked field-by-field
    # below, so this only has to be good enough to surface candidate matches.
    search_text = " ".join(t for t in (args.manufacturer, args.series) if t)

    host = SANDBOX_HOST if args.sandbox else PROD_HOST

    output_path = args.output
    if not output_path:
        safe_kw = "".join(c if c.isalnum() else "_" for c in search_text)[:40].strip("_") or "digikey_export"
        output_path = f"{safe_kw}.csv"

    auth = DigiKeyAuth(client_id, client_secret, host)
    client = DigiKeyClient(
        auth,
        host,
        client_id,
        locale_site=args.locale_site,
        locale_language=args.locale_language,
        locale_currency=args.locale_currency,
    )

    if args.verbose:
        print(f"Searching {host} for manufacturer={args.manufacturer!r} series={args.series!r} "
              f"(search text: {search_text!r})", file=sys.stderr)

    rows: list[dict] = []
    try:
        for product in iter_filtered_products(
            client,
            keywords=search_text,
            manufacturer=args.manufacturer,
            series=args.series,
            page_size=args.page_size,
            max_pages=args.max_pages,
            verbose=args.verbose,
        ):
            rows.append(flatten_product(product))
            if args.max_results and len(rows) >= args.max_results:
                break
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    count = write_csv(rows, output_path)
    print(f"Wrote {count} rows to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())