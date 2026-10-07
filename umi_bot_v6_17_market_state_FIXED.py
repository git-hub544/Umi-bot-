"""
========================================================================
UMI_BOT_BUILD = v6.16-5M-ENTRY-STRUCTURE (SMC entry structure shifted from
15M to 5M, opening-range fixed to still span the first 15 real minutes,
stale "MTF 15m trend" message line removed)
If you don't see this exact string ("v6.16-5M-ENTRY-STRUCTURE") near the
top of the file you opened, you are looking at an OLD downloaded copy,
not the current one - re-download from the latest chat message.

v6.16 patch (this change):
  1) Entry-structure timeframe (smc_df) switched from 15-minute candles
     to 5-minute candles - interval="FIFTEEN_MINUTE" -> "FIVE_MINUTE",
     closed-candle window 15 -> 5. This is the timeframe that drives
     BOS/CHOCH, swing points, ATR, VWAP bias, and the SMC chart image.
  2) get_opening_range() no longer assumes "first candle = opening
     range". Since the base candle is now 5m instead of 15m, it
     aggregates the first THREE 5-minute candles of the session so
     the Opening Range still correctly represents 9:15-9:30, not just
     9:15-9:20.
  3) The "MTF (15m) trend: ..." line in the Telegram message (Level 6
     section) has been deleted completely, as requested.
  4) PCR was NOT changed - it was already recalculated from the live
     option chain every cycle, and this bot's cycle already runs every
     5 minutes (see header note below), so PCR was already effectively
     "on 5 minutes". There was no 15m PCR calculation to shift.
  5) All other "15M"/"15m" labels, chart titles, and log/message text
     that referred to the entry-structure timeframe were relabeled to
     "5M"/"5m" so the displayed text matches what the code now does.
     Historical changelog entries below (v6.14.x and earlier) are left
     as-is since they describe old behaviour, not current behaviour.

v6.14.1 patch: SMC confirmation repaired after live dry-run showed
repeated raw sweeps but zero structural confirmations.
  1/2/3) ORB High/Low break no longer scores directly if it's also a
     confirmed liquidity sweep (wick-through + close-back-inside) -
     see the ORB-vs-sweep cancellation right after confirmed_sweeps.
     Session Open stays a VWAP-filter input only; it can no longer
     out-rank a fresh rejection because of the new veto in #4.
  4) New structural_override_veto: fires on sweep+rejection+
     displacement at a zone even BEFORE a full BOS/CHOCH confirms
     (smc_trigger still needs the full chain to become a positive
     BUY/SELL trigger, but the veto no longer waits for it).
  5) "Near zone" tightened from 1 ATR to 0.3 ATR for the location
     filter (near_demand_zone / near_supply_zone).
  6) build_unified_zone now requires >=2 independent confirming
     sources before returning a zone at all - a single lone level no
     longer masquerades as a confluence zone.
  7) smc_zone_score rewritten to require an actual wick-in/close-out
     REJECTION on the last closed candle, not just static distance.
  8) Writing/Unwinding score now uses OI-change MAGNITUDE (not a raw
     strike count) and requires the matching premium move to agree.
  9) Max Pain directional score now gated by days-to-expiry (<=1) and
     skipped when it would fight a confirmed opposite-direction BOS.
  10) Futures weight reset from an un-backtested x2 to FUTURES_WEIGHT=1.
  11) BankNifty/Midcap require a >=0.15% move before scoring at all.
  12) Regime/Context group is now half-weighted into final_score and
      excluded from the 3-of-N group confluence tally (now 3-of-4 core
      groups: Futures/Options/Zones/SMC) - it can nudge the score but
      can't supply a "vote" of its own anymore.
  13) liquidity_map_direction: Volume+OI agreement now ADDS conviction
      on top of a structurally-confirmed sweep instead of being a hard
      AND-gate that could zero out a fully confirmed sweep.
  14) liquidity_map_direction now looks at the last 3 confirmed sweeps
      (majority vote) instead of only the single most recent one.
  15) atr_is_fallback flag added; if the fallback ATR ever fires, the
      final signal is forced to NEUTRAL that cycle (display-only fallback).
  16) SL/Target rebuilt around structural invalidation (opposing zone
      edge / OI support-resistance strike) with ATR used only as a
      MIN/MAX sanity distance cap, not the primary driver.
This build includes (search these exact strings to jump to each):
  - "def get_previous_day_levels"    -> PDH/PDL
  - "def get_previous_week_levels"   -> PWH/PWL
  - "def detect_equal_highs_lows"    -> Equal Highs/Lows (BSL/SSL)
  - "ORB High"                       -> Opening Range as a liquidity pool
========================================================================
UMI BOT v6 - Composite Market Signal Bot (7-LEVEL FRAMEWORK)
Runs as ONE cycle per execution. GitHub Actions calls this script fresh
every 5 minutes during market hours. Previous cycle's data is saved to
state.json so OI/Volume/Price "change" can be calculated correctly
across runs (since GitHub Actions doesn't keep memory between runs).

v6 adds the full 7-level framework on top of v5. Everything below is
NEW in v6 unless marked otherwise:

  LEVEL 1 - Market Regime: adds Opening Range (first three 5m candles
    high/low) as a directional score, and an explicit Volatility
    Regime label (Low/Mid/High) derived from VIX. (VWAP/ATR were
    already in v5.)

  LEVEL 2 - Futures Institutional Positioning (previously MISSING
    entirely - v5 only ever looked at the NIFTY INDEX, never the
    futures contract): NIFTY current-month futures token is now
    auto-discovered from the scrip master every run (no hardcoded
    token to go stale at expiry). Futures LTP + OI are fetched each
    cycle and compared to the previous cycle (state.json) to get real
    Futures Price+OI buildup/unwinding classification. FII index
    futures Long/Short OI (previous session, from NSE's official
    participant-wise OI report) is scraped and turned into a
    long-short ratio + day-over-day trend score.

  LEVEL 3 - Option Chain Positioning (previously only aggregate CE/PE
    totals - no per-strike detail): every strike in the selected
    range now gets its own OI change, premium change, volume, and IV
    (via SmartAPI optionGreek), and is classified into Long Buildup /
    Writing / Short Covering / Unwinding for both CE and PE.

  LEVEL 4 - Institutional Zones (previously MISSING): Max Pain strike
    (standard option-writer-loss-minimization formula), strongest
    Call resistance strike / Put support strike (by OI), OI
    concentration (top-3-strike share of total OI), and fresh
    writing/unwinding strike (largest OI swing this cycle) are all
    now computed from the Level 3 per-strike table.

  LEVEL 5 - Price+Flow Confirmation: the 4-case matrix
    (price up/down x OI up/down) now runs on FUTURES price+OI (the
    real institutional signal), not index price + aggregate option OI
    like in v5.

  LEVEL 6 - SMC: unchanged from v5 (BOS/CHOCH, Order Blocks, FVG,
    Liquidity Sweeps were already implemented there).

  LEVEL 7 - Final Decision: composite score is now built from 5
    independent group scores (Futures / Options Chain / Zones / SMC /
    Regime-Context) instead of one OI-dominated number. A BUY/SELL
    additionally requires at least 3 of these 5 groups to agree in
    direction (confluence), on top of the score threshold and the
    VWAP+session-open filter - so a single level (e.g. option OI)
    can no longer swing the signal alone, per your Level 7 note.

  NOTE ON UNVERIFIED PIECES (flagged honestly, not hidden):
  - SmartAPI's optionGreek() response field names (strikePrice /
    optionType / impliedVolatility) are per Angel One's documented
    shape but were not live-tested here. If IV shows N/A everywhere,
    check this response shape first.
  - NSE's participant-OI CSV (archives.nseindia.com/nsearchives) is a
    static end-of-day file, updated once per day after market close -
    it is NOT intraday data, same limitation as the existing FII/DII
    cash scrape. It also occasionally blocks non-browser requests;
    the retry loop tries the last 6 calendar days and fails soft to
    N/A rather than crashing the run.

v5 fixes vs v4:
  1) Strike range is now VIX-scaled (500/750/1000) instead of fixed +-250,
     so deep ITM/OTM Smart Money positioning isn't missed on big-move days.
  2) Composite score is OI-priority weighted. Volume only adds a
     confirmation bonus when it agrees with OI direction - it can no
     longer swing BUY/SELL on its own during fake breakouts / hedging.
  3) SL/Target are ATR(14, 15m)-scaled instead of fixed 110/150 points.
  4) Final signal uses VWAP + session open (not a slow 1H candle) as
     the directional filter: BUY needs score>=2 AND price above both
     VWAP and session open; SELL needs score<=-2 AND price below both.
  5) Moneycontrol scrapes (FII/DII) now retry with backoff instead of
     going straight to N/A on one failed hit.
  Bonus: SMC candles are fetched ONCE and reused for both the signal
  logic and the chart.

  6) Moneycontrol GIFT Nifty / Crude Oil scraping replaced with Yahoo
     Finance (US markets, Asian markets, European markets, WTI/Brent
     crude, Gold). These now feed a real "Global Cues" component into
     the composite score, not just decorative text in the Telegram
     message. FII/DII stays on Moneycontrol since there's no free
     Yahoo equivalent for it.
     Note: no free/reliable Yahoo ticker exists for actual GIFT Nifty
     futures (that needs an NSE IX data subscription) — ^NSEI (Nifty
     spot) is used as a labelled directional proxy instead of a wrong
     ticker like NQ=F (which is Nasdaq futures, not GIFT Nifty).
  7) SMC add-ons: Order Blocks, Fair Value Gaps (now actually counted
     in the score, not just printed), and wick-based Liquidity Sweep
     / Stop Hunt detection (catches reversals that body-close-only
     BOS/CHOCH would miss).

v6.13 patch (Level 4 OI Support/Resistance):
  1) Resistance/Support strike selection now requires confluence -
     top Total OI AND top Change-in-OI at the same strike (via
     find_confirmed_level()) - instead of picking the strike with
     the single highest Total OI, which can be old parked positioning
     with zero fresh activity today.
  2) Added a rolling 6-cycle (~30 min) Support/Resistance history in
     state.json (sr_history) so level_is_strengthening() can tell if
     the SAME strike is getting consistently bigger Change-in-OI
     cycle after cycle (real institutional defense building) vs a
     one-off spike that's already fading.
  3) sr_score (part of Zones Group Score, feeds final_score) is now
     WEIGHTED by that strength: Strengthening level near price =
     full +/-2, Building (not enough data yet) = +/-1 (old default
     behaviour), Weakening = 0 (a dying level no longer counts toward
     the signal). This is on top of - not instead of - the existing
     score/confluence/VWAP/location-filter gates.

v6.13 patch (Level 3 PCR - from pcr_calculator_v2.py):
  4) PCR is no longer just a display number. Added PCR by Change-in-OI,
     by Volume, and OTM-only PCR alongside the existing OI-based PCR.
     Interpretation is now percentile/z-score based against PCR's own
     rolling history (state.json "pcr_history", up to 300 cycles) -
     not fixed 1.2/0.8 thresholds - so "high" PCR adapts to the
     current regime instead of a static number. Extreme zones
     (top/bottom 10 percentile) are flagged as contrarian-risk and
     deliberately score 0, not blindly trusted as bullish/bearish.
     pcr_score (+1 clear-bullish / -1 clear-bearish / 0 extreme,
     neutral, or warm-up) now feeds into Options Chain Group Score.

v6.13 patch (VIX Analyzer - from vix_analyzer.py):
  5) VIX judged on 3 axes instead of just the raw number: absolute
     band (premium behaviour), historical percentile (is today's VIX
     "high" for THIS market's recent regime), and rate of change
     (spiking vs settling). Also derives an independent VIX-implied
     expected-move support/resistance band (separate from the
     option-OI-based one). vix_signal_score (+1 CALL bias / -1 PUT
     bias / 0 below min confidence) feeds Context Group Score.
     Wired vix_history persistence into save_state() (was being read
     from state.json but never written back) and added the full VIX
     band/percentile/trend/signal readout to the Telegram message.
"""

# ============================================================
# v6.17 SELF-SCHEDULING RUNNER (single file - no separate script
# needed anymore)
#
# On a normal launch (`python3 umi_bot_v6_17_market_state_FIXED.py`)
# this file does NOT immediately run the bot logic below. It first
# becomes its own scheduler: it relaunches ITSELF every 5 minutes, as
# a fresh subprocess, only during market hours (9:15-15:30 IST,
# Mon-Fri). The full bot logic further down in this same file only
# actually runs inside that relaunched subprocess (tagged with a
# hidden --single-cycle flag) - one complete cycle at a time, exactly
# like before, just now triggered automatically instead of needing an
# external cron job / Task Scheduler / separate runner script.
#
# WHY built this way instead of wrapping the whole file in a loop:
# everything below this block is a flat, one-shot script (not inside
# a function) - re-indenting 4000+ existing lines into a loop body by
# hand would be very risky to edit correctly. Relaunching this same
# file as a subprocess gives an identical result (one full, clean run
# every 5 minutes, with a fresh crash boundary each cycle - one bad
# cycle can never take down the whole day) without touching a single
# line of the existing bot logic.
#
# TO START IT: just run this file directly and leave it running.
#   Linux/Mac : nohup python3 umi_bot_v6_17_market_state_FIXED.py >> umi_bot_log.txt 2>&1 &
#   Windows   : python umi_bot_v6_17_market_state_FIXED.py   (in a terminal you leave open)
# ============================================================
import sys as _sys_runner

if "--single-cycle" not in _sys_runner.argv:
    import os as _os_runner
    import subprocess as _subprocess_runner
    import time as _time_runner
    from datetime import datetime as _datetime_runner

    try:
        from zoneinfo import ZoneInfo as _ZoneInfo_runner
        _IST_runner = _ZoneInfo_runner("Asia/Kolkata")
    except Exception:
        _IST_runner = None  # fallback: assumes the machine's system clock is already IST

    _INTERVAL_SECONDS = 5 * 60          # run every 5 minutes
    _CYCLE_TIMEOUT_SECONDS = 180        # kill a single cycle if it hangs past this
    _MARKET_OPEN = (9, 15)              # 9:15 AM IST
    _MARKET_CLOSE = (15, 30)            # 3:30 PM IST

    def _now_ist_runner():
        return _datetime_runner.now(_IST_runner) if _IST_runner is not None else _datetime_runner.now()

    def _is_market_hours_runner(dt):
        if dt.weekday() >= 5:  # Sat=5, Sun=6
            return False
        open_t = dt.replace(hour=_MARKET_OPEN[0], minute=_MARKET_OPEN[1], second=0, microsecond=0)
        close_t = dt.replace(hour=_MARKET_CLOSE[0], minute=_MARKET_CLOSE[1], second=0, microsecond=0)
        return open_t <= dt <= close_t

    print(
        "=== UMI BOT self-runner started - will trigger a fresh cycle every "
        f"{_INTERVAL_SECONDS // 60} min, {_MARKET_OPEN[0]:02d}:{_MARKET_OPEN[1]:02d}"
        f"-{_MARKET_CLOSE[0]:02d}:{_MARKET_CLOSE[1]:02d} IST, Mon-Fri ===",
        flush=True,
    )

    while True:
        _dt = _now_ist_runner()
        if _is_market_hours_runner(_dt):
            _ts = _dt.strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{_ts}] ---- Triggering bot cycle ----", flush=True)
            try:
                _result = _subprocess_runner.run(
                    [_sys_runner.executable, __file__, "--single-cycle"],
                    timeout=_CYCLE_TIMEOUT_SECONDS,
                )
                print(f"[{_ts}] Cycle finished, exit code {_result.returncode}", flush=True)
            except _subprocess_runner.TimeoutExpired:
                print(f"[{_ts}] Cycle TIMED OUT after {_CYCLE_TIMEOUT_SECONDS}s - killed, retrying next tick.", flush=True)
            except Exception as _e:
                # This is the key fix: a crash here does NOT kill the
                # runner - only that one cycle is lost, the next 5-min
                # tick still fires normally.
                print(f"[{_ts}] Cycle failed to launch: {type(_e).__name__}: {_e}", flush=True)
        else:
            print(f"[{_dt.strftime('%H:%M:%S')}] Outside market hours - skipping this tick.", flush=True)
        _time_runner.sleep(_INTERVAL_SECONDS)

    _sys_runner.exit(0)  # unreachable - the runner process itself never
                          # falls through to the bot logic below; only a
                          # relaunched --single-cycle subprocess does.

# ============================================================
# Everything from here down is the existing bot logic, UNCHANGED -
# runs exactly once per launch, exactly as it always did. It only
# executes when this file is relaunched with --single-cycle (by the
# runner above), or if you run it manually with that flag yourself
# for a one-off test cycle.
# ============================================================

import os
import json
import time
import math
import statistics
from datetime import datetime, timedelta

import pyotp
import pandas as pd
import numpy as np
import requests
from SmartApi import SmartConnect
import yfinance as yf
from bs4 import BeautifulSoup

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as patches
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

STATE_FILE = "state.json"

# ============================================================
# CREDENTIALS (loaded from environment variables / GitHub Secrets)
# ============================================================

API_KEY = os.environ["ANGEL_API_KEY"]
CLIENT_ID = os.environ["ANGEL_CLIENT_ID"]
MPIN = os.environ["ANGEL_MPIN"]
TOTP_SECRET = os.environ["ANGEL_TOTP_SECRET"]

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def telegram_message(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    try:
        resp = requests.post(url, data=payload, timeout=20)
        if resp.status_code != 200:
            # This is the key debug line: Telegram tells us EXACTLY why
            # a message failed (bad token, chat not found, bot blocked,
            # etc) instead of silently doing nothing.
            print(f"Telegram sendMessage FAILED [{resp.status_code}]: {resp.text}")
        else:
            print("Telegram message sent OK.")
        return resp
    except Exception as e:
        print(f"Telegram sendMessage request error: {e}")
        return None


def telegram_send_photo(path, caption=""):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        with open(path, "rb") as f:
            files = {"photo": f}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption[:1024]}
            resp = requests.post(url, data=data, files=files, timeout=30)
        if resp.status_code != 200:
            print(f"Telegram sendPhoto FAILED [{resp.status_code}]: {resp.text}")
        else:
            print("Telegram photo sent OK.")
        return resp
    except Exception as e:
        print(f"Telegram sendPhoto request error: {e}")
        return None


# ============================================================
# State load/save (replaces Colab's "memory between cycles")
# ============================================================


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return None


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# ============================================================
# FIX #5: Retry helper for flaky external scrapes
# ============================================================


def fetch_with_retry(fn, retries=3, delay=4, label=""):
    """
    Calls fn() up to `retries` times with a short delay between
    attempts. Returns None (never crashes) if every attempt fails,
    so downstream code shows N/A instead of breaking the run.
    """
    for attempt in range(1, retries + 1):
        try:
            result = fn()
            if result is not None:
                return result
        except Exception as e:
            print(f"{label} attempt {attempt}/{retries} failed: {e}")
        if attempt < retries:
            time.sleep(delay)
    print(f"{label}: all {retries} attempts failed, using N/A")
    return None


# ============================================================
# SmartAPI Login
# ============================================================

totp = pyotp.TOTP(TOTP_SECRET).now()
smart = SmartConnect(api_key=API_KEY)
session = smart.generateSession(CLIENT_ID, MPIN, totp)
print("Login Successful")

# ============================================================
# Index Info
# ============================================================

EXCHANGE = "NSE"
NIFTY_SYMBOL = "Nifty 50"
NIFTY_TOKEN = "26000"
NIFTY_HIST_TOKEN = "99926000"  # separate token for historical candle API (LTP token above doesn't work for candles)
MIDCAP_SYMBOL = "Nifty Mid Select"
MIDCAP_TOKEN = "99926074"
BANKNIFTY_SYMBOL = "Nifty Bank"
BANKNIFTY_TOKEN = "99926009"
VIX_SYMBOL = "India VIX"
VIX_TOKEN = "99926017"  # NOTE: verify this token in the scrip master once;
                         # if VIX fetch fails the bot safely falls back to a
                         # fixed mid-range strike width, it will not crash.


def get_ltp(symbol, token):
    data = smart.ltpData(EXCHANGE, symbol, token)
    return float(data["data"]["ltp"])


def get_india_vix():
    try:
        return get_ltp(VIX_SYMBOL, VIX_TOKEN)
    except Exception as e:
        print("VIX fetch error (falling back to fixed strike range):", e)
        return None


# ============================================================
# Download Angel One Scrip Master & Filter NIFTY Options
# ============================================================


def download_scrip_master(url, retries=4, base_delay=8):
    """
    The Angel One scrip master is a large (~35MB) JSON file. On a slow
    or unstable link, GitHub Actions runners sometimes get the
    connection cut mid-download (IncompleteRead) instead of a clean
    timeout.
      - growing backoff between attempts (8s, 16s, 24s...) instead of
        a fixed 5s, giving a throttling/flaky link time to recover
      - much longer read timeout for the large payload
      - Content-Length is checked against what actually arrived, so a
        silently truncated download is caught and retried instead of
        crashing json parsing with a confusing error
      - a browser-style User-Agent, since some CDNs are stricter with
        the default python-requests one
    Retries trimmed from 6 to 4 here because the caller now has a
    disk-cache fallback (see below) — no need to burn 10+ minutes
    retrying before falling back to a known-good cached copy.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            with requests.Session() as s:
                resp = s.get(url, headers=headers, timeout=(15, 180))
                resp.raise_for_status()
                content = resp.content  # requests raises here if the
                                         # transfer was cut short
                expected_len = resp.headers.get("Content-Length")
                if expected_len and len(content) != int(expected_len):
                    raise Exception(
                        f"Incomplete download: got {len(content)} bytes, "
                        f"expected {expected_len} bytes"
                    )
                data = json.loads(content)
                return data  # raw list of dicts, NOT a DataFrame here —
                              # the caller decides whether to cache it
        except Exception as e:
            last_error = e
            print(f"Scrip master download attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                delay = base_delay * attempt
                print(f"Retrying in {delay}s...")
                time.sleep(delay)
    raise Exception(f"Failed to download scrip master after {retries} retries. Last error: {last_error}")


# ============================================================
# Scrip master with disk cache + stale-fallback.
#
# The scrip master rarely changes intraday (only on expiry rollover /
# new contract additions), so we don't need a fresh ~35MB download
# every 5-minute cycle. We cache the last successful download to disk
# and reuse it. If GitHub Actions is configured to persist this file
# across runs via actions/cache (see the .yml snippet you were given),
# it survives between cycles too — so most cycles won't even attempt
# the big download, and the few that do have a safety net if it fails.
# ============================================================

SCRIP_MASTER_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
SCRIP_MASTER_CACHE_FILE = "scrip_master_cache.json"
SCRIP_MASTER_MAX_CACHE_AGE_HOURS = 20  # refresh at most once a day


def load_scrip_master_cache():
    if not os.path.exists(SCRIP_MASTER_CACHE_FILE):
        return None
    try:
        with open(SCRIP_MASTER_CACHE_FILE, "r") as f:
            cached = json.load(f)
        cached_at = datetime.fromisoformat(cached["cached_at"])
        age_hours = (datetime.now() - cached_at).total_seconds() / 3600
        return cached["data"], age_hours
    except Exception as e:
        print("Scrip master cache unreadable, ignoring it:", e)
        return None


def save_scrip_master_cache(data):
    try:
        with open(SCRIP_MASTER_CACHE_FILE, "w") as f:
            json.dump({"cached_at": datetime.now().isoformat(), "data": data}, f)
    except Exception as e:
        print("Could not write scrip master cache (non-fatal):", e)


cache_result = load_scrip_master_cache()
used_stale_cache = False

if cache_result and cache_result[1] < SCRIP_MASTER_MAX_CACHE_AGE_HOURS:
    # Fresh-enough cache on disk (e.g. restored by actions/cache from
    # an earlier cycle today) — skip the big download entirely.
    scrip_data, cache_age = cache_result
    print(f"Using cached scrip master ({cache_age:.1f}h old), skipping download.")
    master_df = pd.DataFrame(scrip_data)
else:
    try:
        scrip_data = download_scrip_master(SCRIP_MASTER_URL)
        save_scrip_master_cache(scrip_data)
        master_df = pd.DataFrame(scrip_data)
        print("Scrip master downloaded fresh and cached.")
    except Exception as e:
        # Fresh download failed after all retries. Fall back to
        # whatever is cached, even if it's older than the normal
        # refresh window, rather than crashing the whole cycle.
        if cache_result:
            scrip_data, cache_age = cache_result
            print(f"Fresh download failed ({e}). Falling back to stale cache ({cache_age:.1f}h old).")
            master_df = pd.DataFrame(scrip_data)
            used_stale_cache = True
        else:
            print("Fresh download failed and no cache exists — cannot continue.")
            raise

option_df = master_df[
    (master_df["exch_seg"] == "NFO") & (master_df["name"] == "NIFTY")
].copy()

option_df["expiry"] = pd.to_datetime(option_df["expiry"])
expiry_list = sorted(option_df["expiry"].dropna().unique())
nearest_expiry = expiry_list[0]

expiry_df = option_df[option_df["expiry"] == nearest_expiry].copy()

# ============================================================
# LEVEL 2 (NEW): NIFTY Futures contract auto-discovery.
# v5 never looked at futures at all - only the index. This finds the
# current-month NIFTY future fresh from the scrip master every run,
# so it never needs a hardcoded token that goes stale at expiry.
# ============================================================

if "instrumenttype" in master_df.columns:
    fut_df = master_df[
        (master_df["exch_seg"] == "NFO") & (master_df["name"] == "NIFTY")
        & (master_df["instrumenttype"] == "FUTIDX")
    ].copy()
else:
    # Defensive fallback in case the scrip master ever drops this column.
    fut_df = master_df[
        (master_df["exch_seg"] == "NFO") & (master_df["name"] == "NIFTY")
        & (master_df["symbol"].astype(str).str.endswith("FUT"))
    ].copy()

fut_df["expiry"] = pd.to_datetime(fut_df["expiry"])
fut_expiry_list = sorted(fut_df["expiry"].dropna().unique())
if len(fut_expiry_list) == 0:
    raise Exception("No NIFTY FUTIDX contract found in scrip master - cannot build Level 2 (Futures) data.")

nearest_fut_expiry = fut_expiry_list[0]
nifty_fut_row = fut_df[fut_df["expiry"] == nearest_fut_expiry].iloc[0]
NIFTY_FUT_TOKEN = str(nifty_fut_row["token"])
NIFTY_FUT_SYMBOL = str(nifty_fut_row["symbol"])
print(f"NIFTY Futures contract: {NIFTY_FUT_SYMBOL} (token {NIFTY_FUT_TOKEN}, expiry {pd.Timestamp(nearest_fut_expiry).date()})")


def get_futures_snapshot(token):
    resp = smart.getMarketData("FULL", {"NFO": [token]})
    row = resp["data"]["fetched"][0]
    return {
        "ltp": float(row["ltp"]),
        "oi": float(row["opnInterest"]),
        "volume": float(row["tradeVolume"]),
    }


# ============================================================
# ATM Strike Selection + FIX #1: VIX-scaled dynamic strike range
# (recalculated fresh every run - NIFTY and VIX both move)
# ============================================================

nifty_ltp = get_ltp(NIFTY_SYMBOL, NIFTY_TOKEN)
midcap_price = get_ltp(MIDCAP_SYMBOL, MIDCAP_TOKEN)
banknifty_price = get_ltp(BANKNIFTY_SYMBOL, BANKNIFTY_TOKEN)
# ============================================================
# VIX fetch frequency (per user request): India VIX moves slowly
# intraday, so instead of re-fetching it every 5-minute cycle, only
# fetch/calculate it TWICE a day - once in the 9:20-9:30 opening
# window and once in the 12:30-13:00 midday window. Every other cycle
# reuses the last fetched value from state.json (no fresh VIX call).
# ============================================================
_vix_cache_state = load_state() or {}
_vix_now_ist = datetime.now() + timedelta(hours=5, minutes=30)
_vix_today_str = _vix_now_ist.strftime("%Y-%m-%d")
_vix_cache_morning_done = _vix_cache_state.get("vix_cache_morning_done", False)
_vix_cache_midday_done = _vix_cache_state.get("vix_cache_midday_done", False)
_vix_cache_value = _vix_cache_state.get("vix_cache_value")

if _vix_cache_state.get("vix_cache_date") != _vix_today_str:
    # New trading day - both twice-a-day slots become available again.
    _vix_cache_morning_done = False
    _vix_cache_midday_done = False

_vix_minutes_now = _vix_now_ist.hour * 60 + _vix_now_ist.minute
_vix_in_morning_window = (9 * 60 + 20) <= _vix_minutes_now <= (9 * 60 + 30)
_vix_in_midday_window = (12 * 60 + 30) <= _vix_minutes_now <= (13 * 60)

if _vix_in_morning_window and not _vix_cache_morning_done:
    india_vix = get_india_vix()
    _vix_cache_morning_done = True
    if india_vix is not None:
        _vix_cache_value = india_vix
    print(f"VIX freshly fetched (9:20-9:30 morning window): {india_vix}")
elif _vix_in_midday_window and not _vix_cache_midday_done:
    india_vix = get_india_vix()
    _vix_cache_midday_done = True
    if india_vix is not None:
        _vix_cache_value = india_vix
    print(f"VIX freshly fetched (12:30-13:00 midday window): {india_vix}")
else:
    india_vix = _vix_cache_value
    print(f"VIX reused from last fetch (outside the two daily VIX windows): {india_vix}")

_vix_cache_date = _vix_today_str

# LEVEL 2 (NEW): futures LTP + OI snapshot for this cycle.
fut_snapshot = fetch_with_retry(
    lambda: get_futures_snapshot(NIFTY_FUT_TOKEN), retries=3, delay=4, label="NIFTY Futures snapshot",
)
if fut_snapshot is None:
    # Graceful fallback: don't crash the whole cycle over one flaky call.
    # Futures group score will just come out neutral (0) this cycle since
    # fut_ltp == nifty_ltp means fut_change/fut_oi_change below will read
    # as "no futures data this cycle" once compared to state.
    fut_snapshot = {"ltp": nifty_ltp, "oi": 0.0, "volume": 0.0}
    print("Futures snapshot fetch failed after retries - Level 2 (Futures) score will be neutral this cycle.")

fut_ltp = fut_snapshot["ltp"]
fut_oi = fut_snapshot["oi"]

ATM_STRIKE = round(nifty_ltp / 50) * 50

# Low VIX (<13)   -> quiet market, +-500 is enough
# Mid  VIX (13-20) -> normal, +-750
# High VIX (>20)  -> big-move / event day, +-1000 so deep ITM/OTM
#                    Smart Money positioning isn't missed
if india_vix is None:
    STRIKE_RANGE = 750  # safe middle default if VIX fetch fails
elif india_vix < 13:
    STRIKE_RANGE = 500
elif india_vix <= 20:
    STRIKE_RANGE = 750
else:
    STRIKE_RANGE = 1000

# LEVEL 1 (NEW): explicit Volatility Regime label (same VIX bands as
# above, just surfaced as its own named signal instead of being buried
# inside the strike-range logic only).
if india_vix is None:
    vol_regime = "Unknown"
elif india_vix < 13:
    vol_regime = "Low"
elif india_vix <= 20:
    vol_regime = "Mid"
else:
    vol_regime = "High"

expiry_df["strike"] = expiry_df["strike"].astype(float) / 100

selected_option = expiry_df[
    (expiry_df["strike"] >= ATM_STRIKE - STRIKE_RANGE)
    & (expiry_df["strike"] <= ATM_STRIKE + STRIKE_RANGE)
].copy()
selected_option = selected_option.sort_values("strike")

CE = selected_option[selected_option["symbol"].str.endswith("CE")]
PE = selected_option[selected_option["symbol"].str.endswith("PE")]

print(f"NIFTY LTP: {nifty_ltp} | ATM: {ATM_STRIKE} | VIX: {india_vix} | "
      f"Range: +/-{STRIKE_RANGE} | CALLs: {len(CE)} | PUTs: {len(PE)}")


def get_option_data(token_list):
    exchange_tokens = {"NFO": token_list}
    resp = smart.getMarketData("FULL", exchange_tokens)
    return pd.DataFrame(resp["data"]["fetched"])


def arrow(x):
    return "↑" if x > 0 else ("↓" if x < 0 else "→")


def classify_price_action(nifty_chg, total_oi_chg):
    if nifty_chg > 0 and total_oi_chg > 0:
        return "LONG BUILD-UP"
    elif nifty_chg < 0 and total_oi_chg > 0:
        return "SHORT BUILD-UP"
    elif nifty_chg < 0 and total_oi_chg < 0:
        return "LONG UNWINDING"
    elif nifty_chg > 0 and total_oi_chg < 0:
        return "SHORT COVERING"
    return "NEUTRAL"


# ============================================================
# Fetch current CE/PE OI & Volume totals
# ============================================================

ce_tokens = CE["token"].tolist()
pe_tokens = PE["token"].tolist()

ce_data = get_option_data(ce_tokens)
pe_data = get_option_data(pe_tokens)

ce_data = ce_data[["tradingSymbol", "symbolToken", "ltp", "opnInterest", "tradeVolume"]]
pe_data = pe_data[["tradingSymbol", "symbolToken", "ltp", "opnInterest", "tradeVolume"]]
ce_data.columns = ["symbol", "token", "ltp", "oi", "volume"]
pe_data.columns = ["symbol", "token", "ltp", "oi", "volume"]
ce_data["token"] = ce_data["token"].astype(str)
pe_data["token"] = pe_data["token"].astype(str)

ce_oi_total = ce_data["oi"].astype(float).sum()
pe_oi_total = pe_data["oi"].astype(float).sum()
ce_vol_total = ce_data["volume"].astype(float).sum()
pe_vol_total = pe_data["volume"].astype(float).sum()

# ============================================================
# LEVEL 3 (NEW): strike-wise CE/PE table. v5 only ever kept the SUM
# across the whole range - this merges the strike price back in
# (token-matched, not symbol-matched, since token is a more reliable
# join key than broker-formatted trading symbol strings) so every
# strike can be tracked individually below.
# ============================================================

CE_tok = CE[["strike", "token"]].copy()
CE_tok["token"] = CE_tok["token"].astype(str)
PE_tok = PE[["strike", "token"]].copy()
PE_tok["token"] = PE_tok["token"].astype(str)

ce_full = CE_tok.merge(ce_data, on="token", how="inner")
pe_full = PE_tok.merge(pe_data, on="token", how="inner")

# Snapshot of this cycle's per-strike OI/LTP, to be saved to state.json
# so next cycle can diff against it (this is what powers Level 3's
# Writing/Unwinding classification below).
current_strike_snapshot = {}
for _, r in ce_full.iterrows():
    key = str(int(r["strike"]))
    current_strike_snapshot.setdefault(key, {})["ce_oi"] = float(r["oi"])
    current_strike_snapshot[key]["ce_ltp"] = float(r["ltp"])
for _, r in pe_full.iterrows():
    key = str(int(r["strike"]))
    current_strike_snapshot.setdefault(key, {})["pe_oi"] = float(r["oi"])
    current_strike_snapshot[key]["pe_ltp"] = float(r["ltp"])

# ============================================================
# Load previous cycle's values from state.json
# ============================================================

state = load_state()

if state is None:
    print(f"[{time.strftime('%H:%M:%S')}] First run - baseline set. NIFTY={nifty_ltp}")
    telegram_message("✅ UMI BOT Started - baseline set. Signals from next cycle onward.")
    save_state({
        "ce_oi": ce_oi_total, "pe_oi": pe_oi_total,
        "ce_vol": ce_vol_total, "pe_vol": pe_vol_total,
        "nifty": nifty_ltp, "midcap": midcap_price,
        "fut_ltp": fut_ltp, "fut_oi": fut_oi,
        "strike_oi": current_strike_snapshot,
        "vix_cache_date": _vix_cache_date,
        "vix_cache_morning_done": _vix_cache_morning_done,
        "vix_cache_midday_done": _vix_cache_midday_done,
        "vix_cache_value": _vix_cache_value,
    })
    raise SystemExit(0)

prev_ce_oi = state["ce_oi"]
prev_pe_oi = state["pe_oi"]
prev_ce_vol = state["ce_vol"]
prev_pe_vol = state["pe_vol"]
prev_nifty = state["nifty"]
prev_midcap = state["midcap"]
prev_banknifty = state.get("banknifty", banknifty_price)
# .get() with a same-value default below: if this is the first cycle
# after upgrading from an old (pre-v6) state.json that doesn't have
# these keys yet, the "change" just reads as 0 instead of crashing.
prev_fut_ltp = state.get("fut_ltp", fut_ltp)
prev_fut_oi = state.get("fut_oi", fut_oi)
prev_strike_state = state.get("strike_oi", {})
prev_fii_fut_ratio = state.get("fii_fut_ratio")  # None until it's run once
# Rolling Support/Resistance history (last N cycles) - powers the
# "is this level strengthening or fading" check below. Only added
# key, older state.json files without it just default to [].
prev_sr_history = state.get("sr_history", [])
prev_vix_history = state.get("vix_history", [])
prev_early_watch = state.get("last_early_watch")  # dedup key for the Early Watch alert
prev_market_behaviour = state.get("market_behaviour", "")
# v6.17 FIX: an open trade (entry/SL/target) was computed fresh every
# cycle and never checked against live price on LATER cycles, so a
# real SL-hit or Target-hit on an already-open call was never reported
# - the bot just printed a brand new NEUTRAL/BUY/SELL as if the earlier
# call never existed. Persist it so it can be tracked.
prev_open_trade = state.get("open_trade")  # dict or None

# ============================================================
# Calculate changes vs previous cycle
# ============================================================

ce_oi_change = ce_oi_total - prev_ce_oi
pe_oi_change = pe_oi_total - prev_pe_oi
ce_vol_change = ce_vol_total - prev_ce_vol
pe_vol_change = pe_vol_total - prev_pe_vol
nifty_change = nifty_ltp - prev_nifty
midcap_change = midcap_price - prev_midcap
banknifty_change = banknifty_price - prev_banknifty

# LEVEL 2 (NEW): futures price + OI change vs previous cycle - this is
# the real institutional Price+OI signal (Level 5's matrix should run
# on this, not on the index + aggregate option OI like v5 did).
fut_change = fut_ltp - prev_fut_ltp
fut_oi_change = fut_oi - prev_fut_oi

# ============================================================
# SMC Suite: HTF Bias + Body-Close BOS/CHOCH + Non-Repainting
# Order Blocks + FVG + Liquidity + Supply/Demand + S/R + ATR
#
# Moved above the score section (needed for FIX #3 and FIX #4):
# HTF bias and ATR now have to exist BEFORE the signal/SL/Target
# are decided, not just get drawn on a chart afterwards.
# ============================================================


def get_historical_candles(token, exchange="NSE", interval="FIFTEEN_MINUTE", days=5):
    to_date = datetime.now() + timedelta(hours=5, minutes=30)
    from_date = to_date - timedelta(days=days)
    params = {
        "exchange": exchange,
        "symboltoken": token,
        "interval": interval,
        "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
        "todate": to_date.strftime("%Y-%m-%d %H:%M"),
    }
    data = smart.getCandleData(params)
    df = pd.DataFrame(data["data"], columns=["time", "open", "high", "low", "close", "volume"])
    df["time"] = pd.to_datetime(df["time"])
    df = df.reset_index(drop=True)
    return df


def keep_only_closed_candles(df, minutes):
    """Remove the currently-forming broker candle before any analysis.

    SmartAPI can return the active candle as the last row. SMC, VWAP,
    rejection and 5M confirmation must use only candles whose interval
    has actually ended.
    """
    if df is None or df.empty or "time" not in df.columns:
        return df
    _x = df.copy()
    # SmartAPI may return timezone-aware timestamps (e.g. UTC+05:30),
    # while older/other responses may be timezone-naive. Normalize BOTH
    # to the same naive IST clock before doing any datetime comparison.
    _times = pd.to_datetime(_x["time"], errors="coerce")
    if getattr(_times.dt, "tz", None) is not None:
        _times = _times.dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    _x["time"] = _times
    _x = _x.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
    _cutoff = pd.Timestamp.now(tz="Asia/Kolkata").tz_localize(None)
    _end = _x["time"] + pd.to_timedelta(minutes, unit="m")
    _x = _x[_end <= _cutoff].reset_index(drop=True)
    return _x


# ---------- Swings ----------
def detect_swings(df, lookback=3):
    swing_high = [False] * len(df)
    swing_low = [False] * len(df)
    for i in range(lookback, len(df) - lookback):
        wh = df["high"].iloc[i - lookback:i + lookback + 1]
        wl = df["low"].iloc[i - lookback:i + lookback + 1]
        if df["high"].iloc[i] == wh.max():
            swing_high[i] = True
        if df["low"].iloc[i] == wl.min():
            swing_low[i] = True
    # Explicit dtype=bool - assigning an empty [] to a DataFrame column
    # (which happens whenever candle fetch fails and df has 0 rows)
    # silently makes it float64 instead of bool. That broke boolean-mask
    # filtering later (recent[recent["swing_high"]]) with a confusing
    # "KeyError: 'high'" instead of a clean empty result.
    df["swing_high"] = pd.Series(swing_high, dtype=bool, index=df.index)
    df["swing_low"] = pd.Series(swing_low, dtype=bool, index=df.index)
    return df


def label_market_structure(df):
    """
    Walks swing points chronologically and labels each relative to the
    previous swing of the SAME type: Swing High -> "HH"/"LH", Swing Low
    -> "HL"/"LL". An uptrend is a sequence of HH+HL; a downtrend is a
    sequence of LH+LL - this is the real structural basis behind a
    genuine BOS/CHOCH read.
    """
    points = []
    last_high = None
    last_low = None
    for i in range(len(df)):
        row = df.iloc[i]
        if row["swing_high"]:
            label = "HH" if (last_high is not None and row["high"] > last_high) else "LH" if last_high is not None else "H"
            last_high = row["high"]
            points.append({"time": row["time"], "price": float(row["high"]), "kind": "high", "label": label})
        if row["swing_low"]:
            label = "HL" if (last_low is not None and row["low"] > last_low) else "LL" if last_low is not None else "L"
            last_low = row["low"]
            points.append({"time": row["time"], "price": float(row["low"]), "kind": "low", "label": label})
    points.sort(key=lambda p: p["time"])
    return points


# ---------- BOS/CHOCH: body-close confirmed, with a minimum buffer
# to filter out marginal liquidity-sweep style fakeouts ----------
def detect_bos_choch(df, buffer_pct=0.02):
    """
    BOS/CHOCH from confirmed swing structure.

    IMPORTANT FIX:
    The old detector used a relatively large fixed percentage buffer and
    cleared the swing immediately after a break. That made a genuine
    post-sweep structure break easy to miss on NIFTY 5m candles.

    Now:
      - structure is still based ONLY on confirmed swing highs/lows;
      - confirmation is by candle CLOSE, never by wick;
      - the default buffer is 0.02% (~4.8 pts around 24,000), rather than
        0.05% (~12 pts), so marginal noise is filtered without demanding
        an unnecessarily large move;
      - a broken level is consumed, preventing repeated BOS labels from
        the same swing;
      - the first break establishes trend without inventing a CHOCH.
    """
    events = []
    last_high = None
    last_low = None
    trend = None
    for i in range(len(df)):
        row = df.iloc[i]

        # A swing becomes available only AFTER its confirmation window has
        # completed (detect_swings marks centred swings), so it is safe to
        # use here as historical structure.
        if bool(row.get("swing_high", False)):
            last_high = float(row["high"])
        if bool(row.get("swing_low", False)):
            last_low = float(row["low"])

        close = float(row["close"])
        high_break = last_high is not None and close > last_high * (1 + buffer_pct / 100)
        low_break = last_low is not None and close < last_low * (1 - buffer_pct / 100)

        # If one candle breaks both sides, do not manufacture two structure
        # events; keep the side with the larger normalized displacement.
        if high_break and low_break:
            high_excess = close - last_high
            low_excess = last_low - close
            if high_excess >= low_excess:
                low_break = False
            else:
                high_break = False

        if high_break:
            label = "CHOCH (Bullish)" if trend == "down" else "BOS (Bullish)" if trend == "up" else None
            if label is not None:
                events.append((row["time"], label, close))
            trend = "up"
            last_high = None

        elif low_break:
            label = "CHOCH (Bearish)" if trend == "up" else "BOS (Bearish)" if trend == "down" else None
            if label is not None:
                events.append((row["time"], label, close))
            trend = "down"
            last_low = None

    return events, trend

# ============================================================
# SMC ADD-ON: Order Blocks, Fair Value Gaps (FVG), Supply/Demand
# These were mentioned in the earlier docstring but were never
# actually implemented - this is the real logic for them.
# ============================================================

def detect_order_blocks(df, bos_choch_events, atr_value, lookback=50, volume_mult=1.3, displacement_mult=1.2):
    """
    An Order Block is only created when ALL of these hold for the
    displacement candle (the one breaking the opposing candle's high/low):
      1. STRUCTURE: its timestamp matches an actual confirmed BOS/CHOCH
         event from detect_bos_choch() - a genuine swing-point break,
         not just breaking the immediately preceding candle.
      2. DISPLACEMENT: its candle range (high-low) is >= displacement_mult
         x ATR - a real momentum move, not small drift.
      3. VOLUME: volume spike vs the lookback-window average - falls
         back to price-action-only if volume data is unusable (e.g.
         NIFTY INDEX, which always reports 0 volume - same fix as
         get_vwap_bias()'s own zero-volume fallback above).
    Each zone also carries "mitigated": True if any LATER candle in
    `df` has traded back into its price range (zone consumed/invalid).
    """
    obs = []
    recent = df.tail(lookback).reset_index(drop=True)
    if recent.empty or "volume" not in recent.columns or atr_value is None:
        return obs
    avg_volume = recent["volume"].mean()
    volume_data_usable = avg_volume > 0
    bos_choch_times = {ev_time for ev_time, ev_label, ev_price in bos_choch_events}

    for i in range(len(recent) - 1):
        row = recent.iloc[i]
        nxt = recent.iloc[i + 1]
        is_red = row["close"] < row["open"]
        is_green = row["close"] > row["open"]

        if nxt["time"] not in bos_choch_times:
            continue  # no genuine BOS/CHOCH behind this break - skip
        if (nxt["high"] - nxt["low"]) < displacement_mult * atr_value:
            continue  # broke structure but weak/low-momentum candle - skip
        volume_confirmed = (not volume_data_usable) or (nxt["volume"] >= volume_mult * avg_volume)
        if not volume_confirmed:
            continue  # no volume footprint on the displacement candle - skip

        ob_top, ob_bottom = float(row["high"]), float(row["low"])
        # Mitigation check starts AFTER the displacement candle (nxt),
        # not after the base candle (row) - nxt itself naturally sweeps
        # through the zone on its way out (that's what displacement
        # means), so starting from row["time"] falsely flagged almost
        # every freshly-formed OB as already mitigated on arrival.
        later = recent[recent["time"] > nxt["time"]]
        mitigated = bool(((later["low"] <= ob_top) & (later["high"] >= ob_bottom)).any())

        if is_red and nxt["close"] > row["high"]:
            obs.append({"type": "bullish", "time": row["time"], "top": ob_top, "bottom": ob_bottom, "mitigated": mitigated})
        if is_green and nxt["close"] < row["low"]:
            obs.append({"type": "bearish", "time": row["time"], "top": ob_top, "bottom": ob_bottom, "mitigated": mitigated})
    return obs


def detect_fvg(df, lookback=50, volume_mult=1.3):
    """
    3-candle Fair Value Gap (imbalance):
    Bullish FVG: candle[i-1].high < candle[i+1].low  (gap left behind on a rally)
    Bearish FVG: candle[i-1].low  > candle[i+1].high (gap left behind on a selloff)
    Volume-confirmed on the middle impulse candle (falls back to
    price-action-only when volume data is unusable, e.g. NIFTY INDEX).
    Each gap carries "mitigated": True if a later candle traded back
    into the gap's range (filled = no longer a valid, tradeable FVG).
    """
    fvgs = []
    recent = df.tail(lookback).reset_index(drop=True)
    if recent.empty or "volume" not in recent.columns:
        return fvgs
    avg_volume = recent["volume"].mean()
    volume_data_usable = avg_volume > 0
    for i in range(1, len(recent) - 1):
        c1 = recent.iloc[i - 1]
        c2 = recent.iloc[i]
        c3 = recent.iloc[i + 1]
        volume_confirmed = (not volume_data_usable) or (c2["volume"] >= volume_mult * avg_volume)
        if not volume_confirmed:
            continue  # gap with no volume footprint on the impulse candle - skip, treat as noise
        later = recent.iloc[i + 2:]
        if c1["high"] < c3["low"]:
            gap_top, gap_bottom = float(c3["low"]), float(c1["high"])
            mitigated = bool(((later["low"] <= gap_top) & (later["high"] >= gap_bottom)).any())
            fvgs.append({"type": "bullish", "time": recent.iloc[i]["time"], "top": gap_top, "bottom": gap_bottom, "mitigated": mitigated})
        if c1["low"] > c3["high"]:
            gap_top, gap_bottom = float(c1["low"]), float(c3["high"])
            mitigated = bool(((later["low"] <= gap_top) & (later["high"] >= gap_bottom)).any())
            fvgs.append({"type": "bearish", "time": recent.iloc[i]["time"], "top": gap_top, "bottom": gap_bottom, "mitigated": mitigated})
    return fvgs


def nearest_supply_demand(current_price, order_blocks):
    """
    Treats unmitigated (fresh) bullish order blocks below current price
    as 'demand zones', and unmitigated bearish order blocks above
    current price as 'supply zones'. Returns the nearest one of each.
    """
    demand_zones = [ob for ob in order_blocks
                     if ob["type"] == "bullish" and ob["top"] <= current_price and not ob.get("mitigated", False)]
    supply_zones = [ob for ob in order_blocks
                     if ob["type"] == "bearish" and ob["bottom"] >= current_price and not ob.get("mitigated", False)]
    nearest_demand = max(demand_zones, key=lambda z: z["top"]) if demand_zones else None
    nearest_supply = min(supply_zones, key=lambda z: z["bottom"]) if supply_zones else None
    return nearest_demand, nearest_supply


def nearest_fvg_zones(current_price, fvg_list):
    """
    Same idea but for unmitigated Fair Value Gaps.
    """
    demand_fvgs = [f for f in fvg_list
                    if f["type"] == "bullish" and f["top"] <= current_price and not f.get("mitigated", False)]
    supply_fvgs = [f for f in fvg_list
                    if f["type"] == "bearish" and f["bottom"] >= current_price and not f.get("mitigated", False)]
    nearest_fvg_demand = max(demand_fvgs, key=lambda z: z["top"]) if demand_fvgs else None
    nearest_fvg_supply = min(supply_fvgs, key=lambda z: z["bottom"]) if supply_fvgs else None
    return nearest_fvg_demand, nearest_fvg_supply


# ============================================================
# UNIFIED MULTI-SOURCE SUPPLY/DEMAND ZONES (NEW)
# Previously Demand/Supply was ONLY ever "the nearest unmitigated
# Order Block" - if there was no OB nearby, there was no zone at all,
# even if 4 other independent signals (FVG, option OI, prior swing,
# Equal Highs/Lows, a confirmed liquidity sweep) all agreed on the
# same price area. This combines ALL of them:
#   Demand: Bullish OB, Bullish FVG, PE OI Support, Prior Swing Low,
#           Equal Lows (SSL), confirmed bullish Liquidity Sweep
#   Supply: Bearish OB, Bearish FVG, CE OI Resistance, Prior Swing
#           High, Equal Highs (BSL), confirmed bearish Liquidity Sweep
# Sources whose price levels sit within 0.5 ATR of each other get
# clustered into ONE zone; the cluster with the most agreeing sources
# becomes the primary zone, carrying a "strength" count and the list
# of exactly which sources confirmed it (shown in the message + chart).
# ============================================================

def collect_zone_sources(current_price, order_blocks, fvg_list, oi_level, swing_level, equal_level, sweep_events, is_demand):
    sources = []
    ob_type = "bullish" if is_demand else "bearish"
    for ob in order_blocks:
        if ob["type"] == ob_type and not ob.get("mitigated", False):
            if (is_demand and ob["top"] <= current_price) or (not is_demand and ob["bottom"] >= current_price):
                sources.append({"label": ("Bullish OB" if is_demand else "Bearish OB"), "top": ob["top"], "bottom": ob["bottom"]})
    for f in fvg_list:
        if f["type"] == ob_type and not f.get("mitigated", False):
            if (is_demand and f["top"] <= current_price) or (not is_demand and f["bottom"] >= current_price):
                sources.append({"label": ("Bullish FVG" if is_demand else "Bearish FVG"), "top": f["top"], "bottom": f["bottom"]})
    if oi_level is not None and ((is_demand and oi_level <= current_price) or (not is_demand and oi_level >= current_price)):
        sources.append({"label": ("PE OI Support" if is_demand else "CE OI Resistance"), "top": oi_level, "bottom": oi_level})
    if swing_level is not None and ((is_demand and swing_level <= current_price) or (not is_demand and swing_level >= current_price)):
        sources.append({"label": ("Prior Swing Low" if is_demand else "Prior Swing High"), "top": swing_level, "bottom": swing_level})
    if equal_level is not None and ((is_demand and equal_level <= current_price) or (not is_demand and equal_level >= current_price)):
        sources.append({"label": ("Equal Lows (SSL)" if is_demand else "Equal Highs (BSL)"), "top": equal_level, "bottom": equal_level})
    sweep_type = "bullish_sweep" if is_demand else "bearish_sweep"
    for s in sweep_events:
        if s.get("type") == sweep_type:
            lvl = s.get("level")
            if lvl is not None and ((is_demand and lvl <= current_price) or (not is_demand and lvl >= current_price)):
                sources.append({"label": f"Liquidity Sweep ({s.get('label','')})", "top": lvl, "bottom": lvl})
    return sources


def cluster_and_pick_zone(sources, tolerance):
    """
    Greedily clusters sources whose midpoints sit within `tolerance` of
    each other, then returns the cluster with the MOST confirming
    sources - more agreement = a stronger, more trustworthy zone.
    """
    if not sources:
        return None
    ordered = sorted(sources, key=lambda s: (s["top"] + s["bottom"]) / 2)
    clusters = []
    for s in ordered:
        mid = (s["top"] + s["bottom"]) / 2
        placed = False
        for c in clusters:
            if abs(mid - c["_last_mid"]) <= tolerance:
                c["top"] = max(c["top"], s["top"])
                c["bottom"] = min(c["bottom"], s["bottom"])
                c["sources"].append(s["label"])
                c["_last_mid"] = mid
                placed = True
                break
        if not placed:
            clusters.append({"top": s["top"], "bottom": s["bottom"], "sources": [s["label"]], "_last_mid": mid})
    for c in clusters:
        c["strength"] = len(c["sources"])
        del c["_last_mid"]
    clusters.sort(key=lambda c: -c["strength"])
    best = clusters[0]
    MIN_ZONE_CONFLUENCE = 2  # v6.14 fix #6: a single lone source is a level, not a "zone"
    if best["strength"] < MIN_ZONE_CONFLUENCE:
        return None
    return best


def build_unified_zone(current_price, order_blocks, fvg_list, oi_level, swing_level, equal_level,
                        sweep_events, atr_value, is_demand):
    sources = collect_zone_sources(current_price, order_blocks, fvg_list, oi_level, swing_level, equal_level, sweep_events, is_demand)
    tolerance = max((atr_value or 0) * 0.5, 1)
    return cluster_and_pick_zone(sources, tolerance)

def build_mtf_supply_demand_zone(current_price, timeframe_data, is_demand, atr_value):
    """
    Higher-timeframe Supply/Demand zone built ONLY from 1H + 30M price
    structure.  5M is deliberately kept for entry timing, not for
    defining the main zone.

    Each timeframe contributes fresh/unmitigated Order Blocks and FVGs.
    When 1H and 30M sources cluster around the same price, the resulting
    zone records both timeframes as confluence.
    """
    sources = []
    ob_type = "bullish" if is_demand else "bearish"
    for tf, data in timeframe_data.items():
        for ob in data.get("order_blocks", []):
            if ob.get("type") != ob_type or ob.get("mitigated", False):
                continue
            if (is_demand and ob["top"] <= current_price) or (not is_demand and ob["bottom"] >= current_price):
                sources.append({
                    "label": f"{tf} {'Demand OB' if is_demand else 'Supply OB'}",
                    "top": float(ob["top"]), "bottom": float(ob["bottom"]),
                    "timeframe": tf,
                })
        for fvg in data.get("fvg", []):
            if fvg.get("type") != ob_type or fvg.get("mitigated", False):
                continue
            if (is_demand and fvg["top"] <= current_price) or (not is_demand and fvg["bottom"] >= current_price):
                sources.append({
                    "label": f"{tf} {'Demand FVG' if is_demand else 'Supply FVG'}",
                    "top": float(fvg["top"]), "bottom": float(fvg["bottom"]),
                    "timeframe": tf,
                })

    if not sources:
        return None

    tolerance = max((atr_value or 0) * 0.5, 1)
    ordered = sorted(sources, key=lambda x: (x["top"] + x["bottom"]) / 2)
    clusters = []
    for src in ordered:
        mid = (src["top"] + src["bottom"]) / 2
        placed = False
        for cluster in clusters:
            if abs(mid - cluster["last_mid"]) <= tolerance:
                cluster["top"] = max(cluster["top"], src["top"])
                cluster["bottom"] = min(cluster["bottom"], src["bottom"])
                cluster["sources"].append(src["label"])
                cluster["timeframes"].add(src["timeframe"])
                cluster["last_mid"] = mid
                placed = True
                break
        if not placed:
            clusters.append({
                "top": src["top"], "bottom": src["bottom"],
                "sources": [src["label"]], "timeframes": {src["timeframe"]},
                "last_mid": mid,
            })

    # Prefer zones with both 1H and 30M confluence. If none overlap, use
    # the strongest/freshest higher-timeframe zone rather than inventing one.
    for c in clusters:
        c["strength"] = len(c["sources"])
        c["mtf_confluence"] = len(c["timeframes"])
        c["timeframes"] = "+".join(sorted(c["timeframes"], key=lambda x: {"1H": 0, "30M": 1}.get(x, 9)))
        c.pop("last_mid", None)

    clusters.sort(key=lambda c: (c["mtf_confluence"], c["strength"]), reverse=True)
    return clusters[0]


def detect_liquidity_sweeps(df, lookback=50, wick_buffer_pct=0.02):
    """
    Liquidity Sweep / Stop Hunt: price WICKS beyond a recent swing
    high/low (grabbing the stop-loss orders resting there) but the
    candle CLOSES back inside the prior range - unlike a genuine
    BOS/CHOCH, which closes beyond it. This is the classic "Smart
    Money hunts liquidity before reversing" pattern that body-close
    based BOS/CHOCH detection alone cannot see.
    """
    sweeps = []
    recent = df.tail(lookback).reset_index(drop=True)
    last_swing_high = None
    last_swing_low = None
    for i in range(len(recent)):
        row = recent.iloc[i]
        if row.get("swing_high"):
            last_swing_high = row["high"]
        if row.get("swing_low"):
            last_swing_low = row["low"]

        # Bearish sweep: wick pierces above the last swing high but the
        # candle closes back BELOW it (buy-side liquidity grabbed, then
        # rejected - often a bearish reversal signal).
        if (last_swing_high is not None
                and row["high"] > last_swing_high * (1 + wick_buffer_pct / 100)
                and row["close"] < last_swing_high):
            sweeps.append({"type": "bearish_sweep", "time": row["time"],
                            "level": float(last_swing_high), "wick": float(row["high"])})

        # Bullish sweep: wick pierces below the last swing low but the
        # candle closes back ABOVE it (sell-side liquidity grabbed, then
        # rejected - often a bullish reversal signal).
        if (last_swing_low is not None
                and row["low"] < last_swing_low * (1 - wick_buffer_pct / 100)
                and row["close"] > last_swing_low):
            sweeps.append({"type": "bullish_sweep", "time": row["time"],
                            "level": float(last_swing_low), "wick": float(row["low"])})
    return sweeps


def liquidity_sweep_score(sweeps, df, recency=5):
    """
    Only counts a sweep if it happened within the last `recency`
    candles - an old sweep from hours ago is stale and shouldn't
    move today's signal.
    """
    if not sweeps or df.empty:
        return 0
    recent_times = set(df["time"].tail(recency))
    recent_sweeps = [s for s in sweeps if s["time"] in recent_times]
    if not recent_sweeps:
        return 0
    latest = recent_sweeps[-1]
    return 1 if latest["type"] == "bullish_sweep" else -1


# ============================================================
# LIQUIDITY MAP (NEW): PDH/PDL, PWH/PWL, Equal Highs/Lows (BSL/SSL),
# nearest Swing High/Low, Opening Range High/Low - then a generalized
# sweep detector across ALL of them (not just the rolling swing that
# detect_liquidity_sweeps above checks), plus a strict confirmation
# chain (Rejection -> Displacement -> BOS/CHOCH -> Volume+OI) before
# any of it is allowed to move the score.
# ============================================================

def get_previous_day_levels(df):
    """Previous COMPLETE trading day's High/Low (PDH/PDL) - major
    higher-timeframe liquidity resting just beyond yesterday's range."""
    if df is None or df.empty:
        return None, None
    d = df.copy()
    d["date"] = d["time"].dt.date
    today = (datetime.now() + timedelta(hours=5, minutes=30)).date()
    prior_dates = sorted(x for x in d["date"].unique() if x < today)
    if not prior_dates:
        return None, None
    day_df = d[d["date"] == prior_dates[-1]]
    return float(day_df["high"].max()), float(day_df["low"].min())


def get_previous_week_levels(df):
    """Previous COMPLETE ISO week's High/Low (PWH/PWL) - higher-
    timeframe liquidity one level up from PDH/PDL."""
    if df is None or df.empty:
        return None, None
    d = df.copy()
    iso = d["time"].dt.isocalendar()
    d["wk"] = iso.year.astype(str) + "-W" + iso.week.astype(str).str.zfill(2)
    now_ist = datetime.now() + timedelta(hours=5, minutes=30)
    iso_now = now_ist.isocalendar()
    current_wk = f"{iso_now.year}-W{iso_now.week:02d}"
    prior_weeks = sorted(w for w in d["wk"].unique() if w < current_wk)
    if not prior_weeks:
        return None, None
    wk_df = d[d["wk"] == prior_weeks[-1]]
    return float(wk_df["high"].max()), float(wk_df["low"].min())


def detect_equal_highs_lows(df, lookback=100, tolerance_pct=0.05):
    """
    Equal Highs = 2+ swing highs clustered within `tolerance_pct`% of
    each other -> a Buy-Side Liquidity (BSL) pool: stop-losses of
    shorts + breakout-buy orders resting just above.
    Equal Lows = mirror -> Sell-Side Liquidity (SSL) pool below.
    Returns (list_of_BSL_levels, list_of_SSL_levels).
    """
    if df is None or df.empty or "swing_high" not in df.columns or "swing_low" not in df.columns:
        return [], []  # e.g. this cycle's candle fetch got rate-limited - fail soft, not a crash

    recent = df.tail(lookback)
    highs = recent[recent["swing_high"]]["high"].tolist()
    lows = recent[recent["swing_low"]]["low"].tolist()

    def cluster(values):
        values = sorted(values)
        clusters = []
        for v in values:
            placed = False
            for c in clusters:
                if abs(v - c[-1]) <= c[-1] * tolerance_pct / 100:
                    c.append(v)
                    placed = True
                    break
            if not placed:
                clusters.append([v])
        return [sum(c) / len(c) for c in clusters if len(c) >= 2]

    return cluster(highs), cluster(lows)


def nearest_level(levels, price, above=True):
    """Nearest liquidity level to current price on the requested side -
    the closest pool is the one most likely to get swept next."""
    if not levels:
        return None
    side = [l for l in levels if (l > price if above else l < price)]
    if side:
        return min(side) if above else max(side)
    return min(levels, key=lambda l: abs(l - price))


def detect_level_sweep(df, level_price, lookback=10, wick_buffer_pct=0.02):
    """Wick pierces a FIXED level (PDH/PDL/PWH/PWL/Equal High-Low/ORB -
    not a rolling swing) and closes back on the origin side = sweep."""
    if level_price is None or df is None or df.empty:
        return None
    recent = df.tail(lookback).reset_index(drop=True)
    # IMPORTANT: return the MOST RECENT sweep, not the first historical
    # hit in the lookback. The old forward loop could keep an older sweep
    # alive while a fresh sweep had already happened, making confirmation
    # look for BOS/CHOCH after the wrong candle and producing false NEUTRAL.
    for i in range(len(recent) - 1, -1, -1):
        row = recent.iloc[i]
        if row["high"] > level_price * (1 + wick_buffer_pct / 100) and row["close"] < level_price:
            return {"type": "bearish_sweep", "time": row["time"],
                    "level": float(level_price), "wick": float(row["high"])}
        if row["low"] < level_price * (1 - wick_buffer_pct / 100) and row["close"] > level_price:
            return {"type": "bullish_sweep", "time": row["time"],
                    "level": float(level_price), "wick": float(row["low"])}
    return None


def confirm_sweep(sweep, df, smc_events, atr, displacement_mult=0.8, confirm_window=8):
    """
    Sweep confirmation without the old over-tight gate.

    Rejection is already guaranteed by detect_level_sweep(). After that we
    need genuine follow-through: a directional displacement candle and a
    matching body-close BOS/CHOCH soon after the sweep. Eight 5m candles
    gives the market enough time to complete the structural reversal while
    still keeping the sweep fresh.
    """
    if sweep is None or atr is None or atr == 0 or df is None or df.empty:
        return False
    sweep_time = sweep["time"]
    after = df[df["time"] > sweep_time].head(confirm_window)
    if after.empty:
        return False

    direction = "up" if sweep["type"] == "bullish_sweep" else "down"

    # The displacement must happen BEFORE the BOS/CHOCH. The old code
    # checked these as two independent yes/no conditions, so a displacement
    # near the start of the window could be paired with a structure event
    # that happened before the actual impulse. That was structurally wrong.
    displaced_times = [
        row["time"] for _, row in after.iterrows()
        if (row["high"] - row["low"]) >= displacement_mult * atr
        and ((direction == "up" and row["close"] > row["open"])
             or (direction == "down" and row["close"] < row["open"]))
    ]
    if not displaced_times:
        return False

    for displacement_time in displaced_times:
        bos_choch_confirmed = any(
            ev_time >= displacement_time and ev_time > sweep_time
            and ev_time <= after["time"].max()
            and ((direction == "up" and "Bullish" in ev_label)
                 or (direction == "down" and "Bearish" in ev_label))
            for ev_time, ev_label, _ in smc_events
        )
        if bos_choch_confirmed:
            return True
    return False


def liquidity_map_direction(confirmed_sweeps, ce_vol_change, pe_vol_change, ce_oi_change, pe_oi_change):
    """
    v6.14 (Amit's points #13/#14):
    LOGIC CHAIN: LIQUIDITY MAP -> BSL/SSL identify -> Sweep -> Rejection
    -> Displacement -> BOS/CHOCH (already required for confirmed_sweeps
    entry via confirm_sweep()) -> Volume+OI adds CONVICTION, no longer
    a mandatory AND-gate that can zero out an already structure-
    confirmed sweep.

    - Looks at the last 3 confirmed sweeps (not just the single most
      recent), so an older still-unmitigated structural sweep isn't
      silently discarded the moment a fresh minor one appears.
    - Base score from structural confirmation alone = +/-1.
      Vol agreement and OI agreement each add +/-1 conviction on top
      (so a fully confirmed chain can reach +/-3), but a mismatch on
      Vol/OI no longer erases a real structural sweep down to 0.
    """
    if not confirmed_sweeps:
        return 0, None
    recent = sorted(confirmed_sweeps, key=lambda s: s["time"])[-3:]
    latest = recent[-1]
    bull_votes = sum(1 for s in recent if s["type"] == "bullish_sweep")
    bear_votes = sum(1 for s in recent if s["type"] == "bearish_sweep")
    if bull_votes == bear_votes:
        direction = 1 if latest["type"] == "bullish_sweep" else -1  # tie -> fall back to freshest
    else:
        direction = 1 if bull_votes > bear_votes else -1

    score = direction  # base conviction from confirmed structure alone
    vol_agrees = (direction == 1 and pe_vol_change > ce_vol_change) or (direction == -1 and ce_vol_change > pe_vol_change)
    oi_agrees = (direction == 1 and pe_oi_change > ce_oi_change) or (direction == -1 and ce_oi_change > pe_oi_change)
    if vol_agrees:
        score += direction
    if oi_agrees:
        score += direction
    return score, latest


def _zone_reaction(last_candle, zone, direction):
    """
    v6.14 (Amit's points #5/#6/#7): a zone only scores if price actually
    REACTED to it on the last closed candle - wicked into the zone but
    CLOSED back outside it (rejection) - same standard already used for
    detect_liquidity_sweeps(). Merely sitting within some ATR distance
    of a zone (old behaviour) proves nothing: price can be 1 ATR away
    with zero reaction, or it can blow straight through the zone and
    still count as "near" under a pure distance check.
    direction: "demand" (bullish reaction) or "supply" (bearish reaction).
    """
    if zone is None or last_candle is None:
        return False
    low, high, close = float(last_candle["low"]), float(last_candle["high"]), float(last_candle["close"])
    if direction == "demand":
        # wicked into/through the zone, but closed back above its top -> holding
        return low <= zone["top"] and close >= zone["top"]
    else:
        # wicked into/through the zone, but closed back below its bottom -> holding
        return high >= zone["bottom"] and close <= zone["bottom"]


def smc_zone_score(last_candle, nearest_demand, nearest_supply,
                    nearest_fvg_demand, nearest_fvg_supply, atr):
    """
    +1 only if the last closed candle actually REACTED off an
       unmitigated demand zone or unfilled bullish FVG (wick in, close
       held above) - not just sitting within distance of one.
    -1 mirror for supply zone / bearish FVG.
    A zone that gets wicked through with a close INSIDE or beyond it
    scores 0 (or negative via the opposite side) - that zone has
    failed, not "given a bullish signal by proximity" (old bug).
    """
    score = 0
    if _zone_reaction(last_candle, nearest_demand, "demand"):
        score += 1
    if _zone_reaction(last_candle, nearest_supply, "supply"):
        score -= 1
    if _zone_reaction(last_candle, nearest_fvg_demand, "demand"):
        score += 1
    if _zone_reaction(last_candle, nearest_fvg_supply, "supply"):
        score -= 1
    return score



def get_vwap_bias(candle_df):
    """
    Computes today's session VWAP and session open from candles
    ALREADY fetched for the MTF/SMC logic (smc_df) - NO separate API
    call. The old version fetched a fresh 5-min series here, which
    kept hitting Angel One's rate limit right after the SMC candle
    fetch, so VWAP was coming back None on almost every run.
    """
    if candle_df is None or len(candle_df) == 0:
        return None, None

    today = (datetime.now() + timedelta(hours=5, minutes=30)).date()
    today_candles = candle_df[candle_df["time"].dt.date == today]
    if today_candles.empty:
        return None, None

    typical_price = (today_candles["high"] + today_candles["low"] + today_candles["close"]) / 3
    volume = today_candles["volume"].astype(float)
    cum_vol = volume.cumsum()
    cum_pv = (typical_price * volume).cumsum()
    if cum_vol.iloc[-1] == 0:
        vwap_value = float(typical_price.mean())
        session_open = float(today_candles["open"].iloc[0])
        return vwap_value, session_open

    vwap_value = float((cum_pv / cum_vol).iloc[-1])
    session_open = float(today_candles["open"].iloc[0])
    return vwap_value, session_open
      # ============================================================
# ATR (Average True Range) - FIX #3: used for dynamic SL/Target
# instead of the old fixed 110/150 point values.
# ============================================================

def calculate_atr(df, period=14):
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    if atr.empty or pd.isna(atr.iloc[-1]):
        return None
    return float(atr.iloc[-1])


# ============================================================
# Bonus: SMC candles (5m) + HTF (1H) bias fetched ONCE here and
# reused for both the signal logic AND the chart below.
# (v4 bug: these were fetched twice - once for logic, once for chart.)
# ============================================================

print("Fetching Supply/Demand (1H + 30M) and entry structure (5M)...")

# HIGHER TIMEFRAMES: 1H + 30M define the main Supply/Demand zones.
htf_1h_df = fetch_with_retry(
    lambda: get_historical_candles(NIFTY_HIST_TOKEN, interval="ONE_HOUR", days=30),
    retries=3, delay=5, label="1H Supply/Demand candles",
)
htf_30m_df = fetch_with_retry(
    lambda: get_historical_candles(NIFTY_HIST_TOKEN, interval="THIRTY_MINUTE", days=20),
    retries=3, delay=5, label="30M Supply/Demand candles",
)

for _name in ("htf_1h_df", "htf_30m_df"):
    _df = locals().get(_name)
    if _df is None or len(_df) == 0:
        locals()[_name] = pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])

htf_1h_df = keep_only_closed_candles(htf_1h_df, 60)
htf_30m_df = keep_only_closed_candles(htf_30m_df, 30)
htf_1h_df = detect_swings(htf_1h_df, lookback=3)
htf_30m_df = detect_swings(htf_30m_df, lookback=3)
htf_1h_events, _htf_1h_trend = detect_bos_choch(htf_1h_df, buffer_pct=0.02)
htf_30m_events, _htf_30m_trend = detect_bos_choch(htf_30m_df, buffer_pct=0.02)

htf_1h_atr = calculate_atr(htf_1h_df, period=14)
htf_30m_atr = calculate_atr(htf_30m_df, period=14)
htf_1h_atr = htf_1h_atr if htf_1h_atr and htf_1h_atr > 0 else None
htf_30m_atr = htf_30m_atr if htf_30m_atr and htf_30m_atr > 0 else None

htf_zone_data = {
    "1H": {
        "order_blocks": detect_order_blocks(htf_1h_df, htf_1h_events, htf_1h_atr, lookback=80) if htf_1h_atr else [],
        "fvg": detect_fvg(htf_1h_df, lookback=80),
    },
    "30M": {
        "order_blocks": detect_order_blocks(htf_30m_df, htf_30m_events, htf_30m_atr, lookback=100) if htf_30m_atr else [],
        "fvg": detect_fvg(htf_30m_df, lookback=100),
    },
}

# ENTRY STRUCTURE: shifted to 5M as the primary structural timeframe
# (was 5M). This candle set drives BOS/CHOCH, swings, ATR, VWAP bias
# and the SMC chart image.
smc_df = fetch_with_retry(
    lambda: get_historical_candles(NIFTY_HIST_TOKEN, interval="FIVE_MINUTE", days=5),
    retries=3, delay=5, label="5M entry structure candles",
)
if smc_df is None or len(smc_df) == 0:
    print("5M candle fetch failed after retries - entry structure unavailable this cycle.")
    smc_df = pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])
smc_df = keep_only_closed_candles(smc_df, 5)
smc_df = detect_swings(smc_df, lookback=3)
smc_events, mtf_trend = detect_bos_choch(smc_df, buffer_pct=0.02)

# entry_5m_df was the separate "entry-refinement" fetch used to check
# the latest reaction on top of the (formerly 5M) structure. Now that
# smc_df itself is 5M, entry_5m_df is the SAME candles re-fetched with
# a shorter swing lookback (2 vs 3). Kept as its own fetch/variable on
# purpose so nothing further down the file that reads entry_5m_df
# separately from smc_df breaks - it is simply no longer a different
# timeframe from smc_df.
entry_5m_df = fetch_with_retry(
    lambda: get_historical_candles(NIFTY_HIST_TOKEN, interval="FIVE_MINUTE", days=5),
    retries=3, delay=5, label="5M entry refinement candles",
)
if entry_5m_df is None or len(entry_5m_df) == 0:
    print("5M entry refinement fetch failed - 5M structure remains the available entry timeframe.")
    entry_5m_df = pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])
entry_5m_df = keep_only_closed_candles(entry_5m_df, 5)
entry_5m_df = detect_swings(entry_5m_df, lookback=2)
print(f"DEBUG smc_df: rows={len(smc_df)} | date_range={smc_df['time'].min()} to {smc_df['time'].max()}")
atr_value = calculate_atr(smc_df, period=14)
atr_is_fallback = False
if atr_value is None or atr_value <= 0:
    atr_value = max(nifty_ltp * 0.003, 20)  # DISPLAY-ONLY fallback: ~0.3% of spot
    atr_is_fallback = True
    print(f"ATR fetch/calc failed - using fallback ATR: {atr_value:.2f} "
          f"(v6.14: signal will be forced NEUTRAL this cycle - see Level 7 decision)")

vwap_value, session_open = get_vwap_bias(smc_df)
if vwap_value is not None and session_open is not None:
    if nifty_ltp > vwap_value and nifty_ltp > session_open:
        vwap_bias = "up"
    elif nifty_ltp < vwap_value and nifty_ltp < session_open:
        vwap_bias = "down"
    else:
        vwap_bias = None  # price is mixed vs VWAP/session open - no clear bias
else:
    vwap_bias = None

print(f"MTF (5m) trend: {mtf_trend} | VWAP: {vwap_value} | Session Open: {session_open} | "
      f"VWAP Bias: {vwap_bias} | ATR(14,5m): {atr_value:.2f}")


# ============================================================
# LEVEL 1 (NEW): Opening Range. smc_df candles are now 5m (was 5m), so
# the 9:15-9:30 opening range is the first THREE 5m candles combined -
# no extra API call, still no reliance on a single 5m candle.
# ============================================================

def get_opening_range(candle_df, candles_per_range=3):
    if candle_df is None or candle_df.empty:
        return None, None
    today = (datetime.now() + timedelta(hours=5, minutes=30)).date()
    today_candles = candle_df[candle_df["time"].dt.date == today].sort_values("time")
    if today_candles.empty:
        return None, None
    first_n = today_candles.iloc[:candles_per_range]
    return float(first_n["high"].max()), float(first_n["low"].min())


or_high, or_low = get_opening_range(smc_df)
orb_score = 0
if or_high is not None and or_low is not None:
    if nifty_ltp > or_high:
        orb_score = 1
    elif nifty_ltp < or_low:
        orb_score = -1

print(f"Opening Range: {or_low}-{or_high} | ORB Score: {orb_score}")


# ============================================================
# LIQUIDITY MAP (NEW): build every major level, then run the full
# Sweep -> Rejection -> Displacement -> BOS/CHOCH -> Volume+OI chain.
# ============================================================

pdh, pdl = get_previous_day_levels(smc_df)
pwh, pwl = get_previous_week_levels(smc_df)
bsl_pool, ssl_pool = detect_equal_highs_lows(smc_df, lookback=100, tolerance_pct=0.05)
bsl_level = nearest_level(bsl_pool, nifty_ltp, above=True)
ssl_level = nearest_level(ssl_pool, nifty_ltp, above=False)

_swing_highs = smc_df[smc_df.get("swing_high", pd.Series(dtype=bool)) == True] if not smc_df.empty else pd.DataFrame()
_swing_lows = smc_df[smc_df.get("swing_low", pd.Series(dtype=bool)) == True] if not smc_df.empty else pd.DataFrame()
recent_swing_high = float(_swing_highs["high"].iloc[-1]) if not _swing_highs.empty else None
recent_swing_low = float(_swing_lows["low"].iloc[-1]) if not _swing_lows.empty else None

liquidity_levels = [
    {"label": "PDH", "price": pdh}, {"label": "PDL", "price": pdl},
    {"label": "PWH", "price": pwh}, {"label": "PWL", "price": pwl},
    {"label": "Equal Highs (BSL)", "price": bsl_level},
    {"label": "Equal Lows (SSL)", "price": ssl_level},
    {"label": "Recent Swing High", "price": recent_swing_high},
    {"label": "Recent Swing Low", "price": recent_swing_low},
    {"label": "ORB High", "price": or_high}, {"label": "ORB Low", "price": or_low},
]
liquidity_levels = [lv for lv in liquidity_levels if lv["price"] is not None]

swept_levels = []
for lv in liquidity_levels:
    hit = detect_level_sweep(smc_df, lv["price"], lookback=10, wick_buffer_pct=0.02)
    if hit:
        hit["label"] = lv["label"]
        swept_levels.append(hit)

confirmed_sweeps = [s for s in swept_levels if confirm_sweep(s, smc_df, smc_events, atr_value)]

# v6.14 fix (Amit's points #2/#3): ORB High/Low is scored as a raw
# breakout AND checked as a liquidity level in the same cycle - if the
# "breakout" is actually a confirmed sweep+rejection back inside the
# range, it's a liquidity grab, not a breakout, and orb_score must not
# stand.
_orb_swept_bearish = any(s["label"] == "ORB High" for s in confirmed_sweeps)  # wicked above, closed back below -> trap for orb_score=+1
_orb_swept_bullish = any(s["label"] == "ORB Low" for s in confirmed_sweeps)   # wicked below, closed back above -> trap for orb_score=-1
if orb_score == 1 and _orb_swept_bearish:
    print("ORB fix: OR High break was a confirmed liquidity sweep (rejection), not a real breakout - orb_score cancelled to 0.")
    orb_score = 0
elif orb_score == -1 and _orb_swept_bullish:
    print("ORB fix: OR Low break was a confirmed liquidity sweep (rejection), not a real breakdown - orb_score cancelled to 0.")
    orb_score = 0

liquidity_score, latest_liquidity_sweep = liquidity_map_direction(
    confirmed_sweeps, ce_vol_change, pe_vol_change, ce_oi_change, pe_oi_change,
)

print(f"Liquidity Map -> PDH:{pdh} PDL:{pdl} PWH:{pwh} PWL:{pwl} BSL:{bsl_level} SSL:{ssl_level} | "
      f"Raw sweeps:{len(swept_levels)} Confirmed(structure):{len(confirmed_sweeps)} "
      f"| Final Liquidity Score:{liquidity_score}"
      + (f" (latest: {latest_liquidity_sweep['label']} {latest_liquidity_sweep['type']})" if latest_liquidity_sweep else ""))


# ============================================================
# FIX #6: Global Cues via Yahoo Finance (replaces old Moneycontrol
# GIFT Nifty / Crude scrape). These now feed a real weighted
# component into the composite score, not just decorative text.
# ============================================================

GLOBAL_TICKERS = {
    "Dow Fut": "YM=F",
    "Nasdaq Fut": "NQ=F",
    "Nikkei 225": "^N225",
    "Hang Seng": "^HSI",
    "FTSE 100": "^FTSE",
    "DAX": "^GDAXI",
    "WTI Crude": "CL=F",
    "Brent Crude": "BZ=F",
    "Gold": "GC=F",
    "GIFT Nifty (proxy: Nifty spot)": "^NSEI",
}


def get_live_price(t):
    """Current/last-traded price - NOT the daily close. Tries fast_info
    first (near-real-time), falls back to the latest 1-minute intraday
    candle if fast_info is unavailable for that ticker."""
    try:
        fi = t.fast_info
        for key in ("last_price", "lastPrice"):
            try:
                val = fi[key]
                if val:
                    return float(val)
            except Exception:
                pass
    except Exception:
        pass
    try:
        intraday = t.history(period="1d", interval="1m")
        if not intraday.empty:
            return float(intraday["Close"].iloc[-1])
    except Exception:
        pass
    return None


def get_prev_close(t, daily_hist):
    try:
        fi = t.fast_info
        for key in ("previous_close", "previousClose"):
            try:
                val = fi[key]
                if val:
                    return float(val)
            except Exception:
                pass
    except Exception:
        pass
    # Fallback: yesterday's daily candle close, from the already-fetched
    # 5-day history (avoids a second API call).
    if daily_hist is not None and len(daily_hist) >= 2:
        return float(daily_hist["Close"].iloc[-2])
    elif daily_hist is not None and len(daily_hist) == 1:
        return float(daily_hist["Close"].iloc[-1])
    return None


def fetch_yahoo_change(ticker):
    """% change of LIVE/current price vs previous close - NOT the old
    close-vs-close-before-that, which was always a day stale."""
    t = yf.Ticker(ticker)
    hist = t.history(period="5d", interval="1d")
    live_price = get_live_price(t)
    prev_close = get_prev_close(t, hist)
    if live_price is None or prev_close is None or prev_close == 0:
        return None
    return round(((live_price - prev_close) / prev_close) * 100, 2)


def get_global_cues():
    cues = {}
    for label, ticker in GLOBAL_TICKERS.items():
        pct = fetch_with_retry(
            lambda t=ticker: fetch_yahoo_change(t),
            retries=2, delay=2, label=f"Yahoo:{label}",
        )
        cues[label] = pct
    return cues


global_cues = get_global_cues()

# Equity indices only contribute to the directional score.
# Crude/Gold/GIFT proxy are shown in the message for context but not
# counted (they don't reliably signal Nifty direction).
EQUITY_CUE_LABELS = ["Dow Fut", "Nasdaq Fut", "Nikkei 225", "Hang Seng", "FTSE 100", "DAX"]
equity_vals = [v for k, v in global_cues.items() if k in EQUITY_CUE_LABELS and v is not None]
avg_global_pct = sum(equity_vals) / len(equity_vals) if equity_vals else 0.0

if avg_global_pct > 0.3:
    global_score = 1
elif avg_global_pct < -0.3:
    global_score = -1
else:
    global_score = 0


# ============================================================
# FIX #5: FII/DII (previous day, cash market) via Moneycontrol,
# now wrapped in fetch_with_retry - falls back to N/A instead of
# crashing the whole run on one bad hit.
# ============================================================

def scrape_fii_dii():
    url = "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table")
    if table is None:
        raise Exception("FII/DII table not found on page")
    rows = table.find_all("tr")[1:3]  # latest date's two rows: FII, DII
    result = {}
    for row in rows:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) >= 4:
            label = cols[1].strip().upper()
            net = cols[-1].replace(",", "")
            result[label] = net
    if not result:
        raise Exception("FII/DII parse produced no rows")
    return result


fii_dii = fetch_with_retry(scrape_fii_dii, retries=3, delay=5, label="FII/DII")
fii_dii = fii_dii or {}
fii_net = fii_dii.get("FII", "N/A")
dii_net = fii_dii.get("DII", "N/A")


# ============================================================
# LEVEL 2 (NEW): FII Index Futures Long/Short positioning, from NSE's
# official participant-wise OI report. This is an END-OF-DAY file
# (previous session), same limitation as the FII/DII cash scrape above
# - NSE does not publish this intraday. Tries the last 6 calendar days
# in case today's file isn't published yet (it drops ~7pm IST).
# ============================================================

def scrape_fii_index_futures():
    ist_now = datetime.now() + timedelta(hours=5, minutes=30)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }
    for back in range(0, 6):
        d = ist_now - timedelta(days=back)
        fname = d.strftime("%d%m%Y")
        url = f"https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_{fname}.csv"
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200 or len(resp.content) < 100:
                continue
            lines = resp.content.decode("utf-8", errors="ignore").splitlines()
            if len(lines) < 3:
                continue
            header = [h.strip().strip('"') for h in lines[1].split(",")]
            for line in lines[2:]:
                cols = [c.strip().strip('"') for c in line.split(",")]
                if len(cols) < 3:
                    continue
                if cols[0].strip().upper() == "FII":
                    row = dict(zip(header, cols))
                    fut_long = float(row.get("Future Index Long", 0) or 0)
                    fut_short = float(row.get("Future Index Short", 0) or 0)
                    return {"long": fut_long, "short": fut_short, "as_of": d.strftime("%Y-%m-%d")}
        except Exception as e:
            print(f"FII index-futures OI scrape failed for {fname}: {e}")
            continue
    return None


fii_fut = fetch_with_retry(scrape_fii_index_futures, retries=1, delay=0, label="FII Index Futures OI")

if fii_fut:
    fii_fut_long = fii_fut["long"]
    fii_fut_short = fii_fut["short"]
    fii_fut_as_of = fii_fut["as_of"]
    fii_fut_ratio = round(fii_fut_long / fii_fut_short, 3) if fii_fut_short else None
else:
    fii_fut_long = fii_fut_short = fii_fut_ratio = fii_fut_as_of = None

fii_fut_score = 0
if fii_fut_ratio is not None and prev_fii_fut_ratio is not None:
    # TREND ONLY, not absolute level. FIIs are structurally net-short
    # index futures almost all the time (it's a hedge against their
    # cash-market long book) - the raw ratio sits well below 1 on
    # basically every trading day. Scoring off the absolute level (the
    # old "bias" logic) meant this silently contributed -1 to the
    # Futures group EVERY cycle regardless of what was actually
    # happening in the market that day - a real bug, not a market read.
    # Whether FIIs are getting MORE or LESS short cycle-to-cycle is the
    # actual signal.
    diff = fii_fut_ratio - prev_fii_fut_ratio
    fii_fut_score = 1 if diff > 0.02 else (-1 if diff < -0.02 else 0)

print(f"FII Index Futures (as of {fii_fut_as_of}): Long={fii_fut_long} Short={fii_fut_short} "
      f"Ratio={fii_fut_ratio} | Score={fii_fut_score}")


# ============================================================
# LEVEL 3 (NEW): Option Greeks / IV per strike, via SmartAPI
# optionGreek(). Field names below are per Angel One's documented
# response shape - NOT live-verified here. This fails soft (empty
# dict -> IV shows N/A) rather than crashing the run if the shape
# has changed; re-check SmartAPI docs if IV is always N/A.
# ============================================================

def get_option_greeks(name, expiry_dt):
    expiry_str = pd.Timestamp(expiry_dt).strftime("%d%b%Y").upper()
    resp = smart.optionGreek({"name": name, "expirydate": expiry_str})
    rows = resp.get("data", []) if isinstance(resp, dict) else []
    iv_map = {}
    for r in rows:
        try:
            k = float(r.get("strikePrice"))
            opt_type = str(r.get("optionType", "")).upper()
            iv = float(r.get("impliedVolatility"))
            side = "CE" if opt_type in ("CE", "CALL") else ("PE" if opt_type in ("PE", "PUT") else None)
            if side:
                iv_map[(k, side)] = iv
        except (TypeError, ValueError):
            continue
    return iv_map


iv_map = fetch_with_retry(
    lambda: get_option_greeks("NIFTY", nearest_expiry), retries=2, delay=3, label="Option Greeks/IV",
) or {}
if not iv_map:
    print("IV fetch returned nothing this cycle - IV will show N/A per strike.")


# ============================================================
# LEVEL 3 (NEW): per-strike table - OI change, premium change, volume,
# IV, and Long Buildup / Writing / Short Covering / Unwinding
# classification for both CE and PE at every strike in range.
# ============================================================

def classify_option_activity(oi_chg, ltp_chg, current_oi):
    thresh = max(current_oi * 0.03, 1)  # ignore sub-3%-of-OI noise
    if abs(oi_chg) < thresh:
        return "Neutral"
    if oi_chg > 0 and ltp_chg > 0:
        return "Long Buildup"
    if oi_chg > 0 and ltp_chg <= 0:
        return "Writing"
    if oi_chg < 0 and ltp_chg > 0:
        return "Short Covering"
    return "Unwinding"


def build_strike_table(ce_full, pe_full, prev_strike_state, iv_map):
    ce_idx = ce_full.set_index("strike")
    pe_idx = pe_full.set_index("strike")
    all_strikes = sorted(set(ce_idx.index) | set(pe_idx.index))
    rows = []
    for k in all_strikes:
        ce_row = ce_idx.loc[k] if k in ce_idx.index else None
        pe_row = pe_idx.loc[k] if k in pe_idx.index else None
        ce_oi = float(ce_row["oi"]) if ce_row is not None else 0.0
        ce_ltp = float(ce_row["ltp"]) if ce_row is not None else 0.0
        ce_vol = float(ce_row["volume"]) if ce_row is not None else 0.0
        pe_oi = float(pe_row["oi"]) if pe_row is not None else 0.0
        pe_ltp = float(pe_row["ltp"]) if pe_row is not None else 0.0
        pe_vol = float(pe_row["volume"]) if pe_row is not None else 0.0

        prev = prev_strike_state.get(str(int(k)), {})
        ce_oi_chg = ce_oi - prev.get("ce_oi", ce_oi)
        ce_ltp_chg = ce_ltp - prev.get("ce_ltp", ce_ltp)
        pe_oi_chg = pe_oi - prev.get("pe_oi", pe_oi)
        pe_ltp_chg = pe_ltp - prev.get("pe_ltp", pe_ltp)

        rows.append({
            "strike": k,
            "ce_oi": ce_oi, "ce_ltp": ce_ltp, "ce_vol": ce_vol,
            "ce_oi_chg": ce_oi_chg, "ce_ltp_chg": ce_ltp_chg,
            "ce_class": classify_option_activity(ce_oi_chg, ce_ltp_chg, ce_oi),
            "ce_iv": iv_map.get((k, "CE")),
            "pe_oi": pe_oi, "pe_ltp": pe_ltp, "pe_vol": pe_vol,
            "pe_oi_chg": pe_oi_chg, "pe_ltp_chg": pe_ltp_chg,
            "pe_class": classify_option_activity(pe_oi_chg, pe_ltp_chg, pe_oi),
            "pe_iv": iv_map.get((k, "PE")),
        })
    return pd.DataFrame(rows)


strike_table = build_strike_table(ce_full, pe_full, prev_strike_state, iv_map)

# Near-ATM (+/-100 pts, i.e. ~2 strikes either side) Writing/Unwinding
# tally - this is what actually distinguishes real Call/Put writing
# pressure from noise far away from the money.
near_atm = strike_table[(strike_table["strike"] - ATM_STRIKE).abs() <= 100]
call_writing_ct = int((near_atm["ce_class"] == "Writing").sum())
call_unwinding_ct = int((near_atm["ce_class"] == "Unwinding").sum())
put_writing_ct = int((near_atm["pe_class"] == "Writing").sum())
put_unwinding_ct = int((near_atm["pe_class"] == "Unwinding").sum())

# v6.14 fix #8: use actual OI-change MAGNITUDE (not a strike count -
# 5 tiny strikes writing shouldn't outweigh 1 strike with 10x the OI),
# and only count a side's OI-change if its premium moved the way real
# writing implies (CE premium falling while CE OI rises = genuine call
# writing; CE premium RISING while OI rises looks more like fresh
# buying mislabelled, or a hedge/spread - excluded from the score).
_ce_writing_mask = (near_atm["ce_class"] == "Writing") & (near_atm["ce_ltp_chg"] <= 0)
_pe_writing_mask = (near_atm["pe_class"] == "Writing") & (near_atm["pe_ltp_chg"] <= 0)
_ce_writing_oi = float(near_atm.loc[_ce_writing_mask, "ce_oi_chg"].sum())
_pe_writing_oi = float(near_atm.loc[_pe_writing_mask, "pe_oi_chg"].sum())
_ce_unwinding_oi = float(near_atm.loc[near_atm["ce_class"] == "Unwinding", "ce_oi_chg"].sum())  # negative
_pe_unwinding_oi = float(near_atm.loc[near_atm["pe_class"] == "Unwinding", "pe_oi_chg"].sum())  # negative

# Put Writing (support building) is bullish, Call Writing (resistance
# building) is bearish; Unwinding on either side is the mirror image.
# Normalize by total near-ATM OI so the score stays on a +/-1 scale
# but now reflects genuine size, not just how many strikes fired.
_total_near_oi = float(near_atm["ce_oi"].sum() + near_atm["pe_oi"].sum()) or 1.0
writing_score_raw = ((_pe_writing_oi - _ce_writing_oi) + (abs(_ce_unwinding_oi) - abs(_pe_unwinding_oi))) / _total_near_oi
writing_score = max(-1, min(1, round(writing_score_raw * 10)))  # scaled - tune the x10 once you've logged a few days of raw ratios

print(f"Near-ATM option activity -> CallWriting:{call_writing_ct} CallUnwinding:{call_unwinding_ct} "
      f"PutWriting:{put_writing_ct} PutUnwinding:{put_unwinding_ct} | "
      f"PremiumAgreed OI ratio:{writing_score_raw:.4f} | Writing Score:{writing_score}")


# ============================================================
# LEVEL 4 (NEW): Institutional Zones - Max Pain, strongest Call
# resistance / Put support strike, OI concentration, fresh
# writing/unwinding strike (largest OI swing this cycle).
# ============================================================

def find_oi_level(strike_table, oi_col):
    """
    v6.17: OI-based level, reported on its own (no ChgOI requirement).
    This is simply the strike carrying the single biggest Total OI pile
    right now - the "heaviest parked contracts" strike. It can be old
    positioning from days ago; it does not need any fresh activity today
    to count. This is what naturally rolls forward strike-to-strike as
    price breaks through one heavy strike and approaches the next one -
    no multi-cycle confirmation wait, it is just whatever the live chain
    shows this cycle. Returns (strike, oi_value).
    """
    if strike_table.empty:
        return None, None
    idx = strike_table[oi_col].idxmax()
    row = strike_table.loc[idx]
    return float(row["strike"]), float(row[oi_col])


def find_chgoi_level(strike_table, chg_col):
    """
    v6.17: ChgOI-based level, reported on its own (no Total-OI requirement).
    This is the strike where the biggest FRESH writing/unwinding happened
    THIS cycle - where option writers are actively acting today, even if
    the total pile sitting there is still small. This is the "live
    conviction" level, separate from the "big old pile" level above.
    Returns (strike, chg_value).
    """
    if strike_table.empty:
        return None, None
    idx = strike_table[chg_col].idxmax()
    row = strike_table.loc[idx]
    return float(row["strike"]), float(row[chg_col])


def build_oi_only_zone(strike, atr_value, source_label):
    """
    v6.17: turns a single option-chain strike (OI-based or ChgOI-based)
    into a small Supply/Demand-style zone (top/bottom band), WITHOUT any
    1H/30M Order Block or FVG confirmation. This is deliberately a
    single-source zone - it is reported on its own in the message, never
    merged into the UNIFIED (1H+30M) Supply/Demand zone's confluence
    count. Band width uses the same 0.3*ATR "near zone" tolerance the
    rest of the bot already uses, centered on the strike.
    """
    if strike is None:
        return None
    half_width = max((atr_value or 0) * 0.3, 1)
    return {
        "top": strike + half_width,
        "bottom": strike - half_width,
        "sources": [source_label],
        "strike": strike,
    }


def level_is_strengthening(history, level_key, chg_key, current_strike, min_points=3):
    """
    Tracks the SAME strike's Change-in-OI across recent 5m cycles.
    True  -> fresh contracts adding every cycle, level genuinely building
    False -> Change in OI shrinking, level losing conviction
    None  -> not enough cycles at this exact strike yet to call it
    """
    vals = [h.get(chg_key) for h in history
            if h.get(level_key) == current_strike and h.get(chg_key) is not None]
    if len(vals) < min_points:
        return None
    recent = vals[-min_points:]
    return all(recent[i] <= recent[i + 1] for i in range(len(recent) - 1))

def calculate_max_pain(strike_table):
    if strike_table.empty:
        return None
    strikes = strike_table["strike"].tolist()
    ce_oi_map = dict(zip(strike_table["strike"], strike_table["ce_oi"]))
    pe_oi_map = dict(zip(strike_table["strike"], strike_table["pe_oi"]))
    best_strike, best_pain = None, None
    for s in strikes:
        pain = (sum(ce_oi_map[k] * max(0, s - k) for k in strikes)
                + sum(pe_oi_map[k] * max(0, k - s) for k in strikes))
        if best_pain is None or pain < best_pain:
            best_pain, best_strike = pain, s
    return best_strike


maxpain_strike = calculate_max_pain(strike_table)
maxpain_dte = (pd.Timestamp(nearest_expiry).date() - (datetime.now() + timedelta(hours=5, minutes=30)).date()).days
maxpain_score = 0
if maxpain_strike is not None and maxpain_dte <= 1:
    # v6.14 fix #9: max pain pinning is only a real force in the last
    # ~1 trading day before expiry. Far from expiry it's context at
    # best, not a directional/reversal signal - scoring it then just
    # fights genuine displacement (BOS) in the opposite direction.
    if nifty_ltp - maxpain_strike > 1.5 * atr_value and mtf_trend != "up":
        maxpain_score = -1  # price stretched above max pain - mild gravitational pull down
    elif maxpain_strike - nifty_ltp > 1.5 * atr_value and mtf_trend != "down":
        maxpain_score = 1   # price stretched below max pain - mild gravitational pull up
elif maxpain_strike is not None:
    print(f"Max Pain score skipped - {maxpain_dte} days to expiry, pinning effect not yet relevant.")

if not strike_table.empty:
    # v6.17: OI-based level and ChgOI-based level are computed and
    # reported SEPARATELY now, instead of requiring both to land on the
    # same strike. "resistance_strike"/"support_strike" = pure Total OI
    # (the heaviest parked strike - rolls forward automatically as price
    # breaks through one and moves toward the next). "resistance_chgoi_
    # strike"/"support_chgoi_strike" = pure Change-in-OI (where fresh
    # writing is happening TODAY, independent of the old pile size).
    resistance_strike, resistance_ce_oi = find_oi_level(strike_table, "ce_oi")
    support_strike, support_pe_oi = find_oi_level(strike_table, "pe_oi")
    resistance_chgoi_strike, resistance_chgoi_value = find_chgoi_level(strike_table, "ce_oi_chg")
    support_chgoi_strike, support_chgoi_value = find_chgoi_level(strike_table, "pe_oi_chg")

    # ChgOI reading specifically AT the OI-based strike (still needed by
    # the "is this OI level strengthening cycle-over-cycle" tracker below
    # - that tracker follows the OI-based strike, not the ChgOI-based one).
    resistance_ce_oi_chg = None
    if resistance_strike is not None:
        _r_row = strike_table.loc[strike_table["strike"] == resistance_strike]
        if not _r_row.empty:
            resistance_ce_oi_chg = float(_r_row["ce_oi_chg"].iloc[0])
    support_pe_oi_chg = None
    if support_strike is not None:
        _s_row = strike_table.loc[strike_table["strike"] == support_strike]
        if not _s_row.empty:
            support_pe_oi_chg = float(_s_row["pe_oi_chg"].iloc[0])

    total_ce_oi = strike_table["ce_oi"].sum()
    total_pe_oi = strike_table["pe_oi"].sum()
    top3_ce = strike_table.nlargest(3, "ce_oi")["ce_oi"].sum()
    top3_pe = strike_table.nlargest(3, "pe_oi")["pe_oi"].sum()
    ce_concentration_pct = round(100 * top3_ce / total_ce_oi, 1) if total_ce_oi else None
    pe_concentration_pct = round(100 * top3_pe / total_pe_oi, 1) if total_pe_oi else None

    max_ce_chg_row = strike_table.loc[strike_table["ce_oi_chg"].idxmax()]
    max_pe_chg_row = strike_table.loc[strike_table["pe_oi_chg"].idxmax()]
    fresh_call_writing_strike = float(max_ce_chg_row["strike"]) if max_ce_chg_row["ce_oi_chg"] > 0 else None
    fresh_put_writing_strike = float(max_pe_chg_row["strike"]) if max_pe_chg_row["pe_oi_chg"] > 0 else None

    # v6.17: OI-based and ChgOI-based Supply/Demand zones, computed
    # STANDALONE from the option chain only - NOT mixed with the 1H/30M
    # Order Block + FVG confirmation that the UNIFIED zone below uses.
    # These are reported as their own separate zone in the message so
    # the option-chain read and the price-structure read stay visible
    # independently instead of being forced into one confluence check.
    #   Resistance strike (CE) = ceiling = Supply.
    #   Support strike (PE)    = floor   = Demand.
    oi_supply_zone = build_oi_only_zone(resistance_strike, atr_value, "OI (big CE pile)")
    oi_demand_zone = build_oi_only_zone(support_strike, atr_value, "OI (big PE pile)")
    chgoi_supply_zone = build_oi_only_zone(resistance_chgoi_strike, atr_value, "ChgOI (fresh CE writing today)")
    chgoi_demand_zone = build_oi_only_zone(support_chgoi_strike, atr_value, "ChgOI (fresh PE writing today)")
else:
    resistance_strike = support_strike = None
    resistance_chgoi_strike = support_chgoi_strike = None
    resistance_chgoi_value = support_chgoi_value = None
    resistance_ce_oi_chg = support_pe_oi_chg = None
    ce_concentration_pct = pe_concentration_pct = None
    fresh_call_writing_strike = fresh_put_writing_strike = None
    oi_supply_zone = oi_demand_zone = None
    chgoi_supply_zone = chgoi_demand_zone = None

# Rolling velocity check: is the SAME resistance/support strike
# getting consistently bigger Change-in-OI cycle after cycle (real
# institutional defense building), or was it a one-cycle spike.
resistance_strengthening = level_is_strengthening(
    prev_sr_history, "resistance_strike", "resistance_chg_oi", resistance_strike)
support_strengthening = level_is_strengthening(
    prev_sr_history, "support_strike", "support_chg_oi", support_strike)

sr_history = (prev_sr_history + [{
    "resistance_strike": resistance_strike, "resistance_chg_oi": resistance_ce_oi_chg,
    "support_strike": support_strike, "support_chg_oi": support_pe_oi_chg,
}])[-6:]  # last 6 cycles = ~30 min rolling window

def _strength_tag(flag, multi_day=None, prev_day_level=None):
    base = "Strengthening" if flag is True else ("Weakening" if flag is False else "Building (need more cycles)")
    if multi_day and prev_day_level is not None:
        base += f" (also held yesterday at {round(prev_day_level,0):.0f})"
    return base

sr_score = 0
# Weighted by level strength, not just raw proximity:
#   Strengthening (fresh OI adding every cycle) -> full +/-2, high conviction
#   Building (not enough cycles yet)            -> +/-1, same as old behaviour
#   Weakening (OI fading at that strike)         -> 0, don't trust a dying level
if support_strike is not None and nifty_ltp >= support_strike and (nifty_ltp - support_strike) <= 0.5 * atr_value:
    if support_strengthening is True:
        sr_score += 2
    elif support_strengthening is False:
        sr_score += 0
    else:
        sr_score += 1
if resistance_strike is not None and nifty_ltp <= resistance_strike and (resistance_strike - nifty_ltp) <= 0.5 * atr_value:
    if resistance_strengthening is True:
        sr_score -= 2
    elif resistance_strengthening is False:
        sr_score -= 0
    else:
        sr_score -= 1

print(f"Max Pain:{maxpain_strike} | Resistance(CE):{resistance_strike} [{_strength_tag(resistance_strengthening)}] "
      f"| Support(PE):{support_strike} [{_strength_tag(support_strengthening)}] "
      f"| SR Score:{sr_score} | MaxPain Score:{maxpain_score} "
      f"| OI Conc CE:{ce_concentration_pct}% PE:{pe_concentration_pct}%")


# ============================================================
# PCR (Put-Call Ratio) by OI, within the selected strike range
# ============================================================

pcr = round(pe_oi_total / ce_oi_total, 2) if ce_oi_total else None

# --- Extended PCR module (from pcr_calculator_v2.py) ---
# Instead of fixed 1.2/0.8 thresholds, PCR is judged against its OWN
# recent history (percentile + z-score) - what counts as "high" PCR
# in a calm week is different from a high-VIX week. Extreme zones are
# flagged as contrarian-risk instead of blindly trusted.

PCR_LOOKBACK_FOR_PERCENTILE = 100   # how many past 5m snapshots to compare against
PCR_TREND_LOOKBACK = 6              # last 6 cycles = ~30 min, for trend direction
PCR_MAX_HISTORY_LEN = 300           # rolling cap so state.json doesn't grow forever

pcr_change_oi = round(pe_oi_change / ce_oi_change, 3) if ce_oi_change else None
pcr_volume = round(pe_vol_total / ce_vol_total, 3) if ce_vol_total else None
if not strike_table.empty:
    _otm_put_oi = strike_table.loc[strike_table["strike"] < nifty_ltp, "pe_oi"].sum()
    _otm_call_oi = strike_table.loc[strike_table["strike"] > nifty_ltp, "ce_oi"].sum()
    pcr_otm = round(_otm_put_oi / _otm_call_oi, 3) if _otm_call_oi else None
else:
    pcr_otm = None


def _pcr_percentile_rank(value, series):
    if not series:
        return 50.0
    below = sum(1 for v in series if v < value)
    return round((below / len(series)) * 100, 1)


def interpret_pcr_adaptive(current_pcr, history, lookback=PCR_LOOKBACK_FOR_PERCENTILE):
    if current_pcr is None:
        return {"label": "N/A", "percentile": None, "z_score": None, "contrarian_watch": False}

    recent = [row["pcr"] for row in history[-lookback:] if row.get("pcr") is not None]
    if len(recent) < 10:
        return {"label": "Insufficient history (warm-up phase)", "percentile": None,
                "z_score": None, "contrarian_watch": False}

    pct = _pcr_percentile_rank(current_pcr, recent)
    mean = statistics.mean(recent)
    stdev = statistics.pstdev(recent) or 0.0001
    z = round((current_pcr - mean) / stdev, 2)

    if pct >= 90:
        label, watch = "Extreme High PCR - strong Put writing, WATCH for contrarian exhaustion", True
    elif pct >= 65:
        label, watch = "Bullish (Put writing dominant)", False
    elif pct <= 10:
        label, watch = "Extreme Low PCR - strong Call writing, WATCH for contrarian exhaustion", True
    elif pct <= 35:
        label, watch = "Bearish (Call writing dominant)", False
    else:
        label, watch = "Neutral / range-bound", False

    return {"label": label, "percentile": pct, "z_score": z, "contrarian_watch": watch}


def detect_pcr_trend(history, lookback=PCR_TREND_LOOKBACK):
    recent = [row["pcr"] for row in history[-lookback:] if row.get("pcr") is not None]
    if len(recent) < 3:
        return "Insufficient data"
    delta = round(recent[-1] - recent[0], 3)
    if delta > 0.05:
        return f"Rising ({delta:+}) - Put writing increasing"
    elif delta < -0.05:
        return f"Falling ({delta:+}) - Call writing increasing"
    return f"Flat ({delta:+})"


prev_pcr_history = state.get("pcr_history", [])
pcr_interpretation = interpret_pcr_adaptive(pcr, prev_pcr_history)
pcr_trend = detect_pcr_trend(prev_pcr_history + [{"pcr": pcr}])
pcr_history = (prev_pcr_history + [{
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "pcr": pcr,
}])[-PCR_MAX_HISTORY_LEN:]

# PCR score - only counts in the CLEAR bullish/bearish percentile
# bands, not the extreme (contrarian-risk) or neutral/warm-up bands,
# so it can't blindly push a signal during a possible exhaustion move.
pcr_score = 0
if pcr_interpretation["label"] == "Bullish (Put writing dominant)":
    pcr_score = 1
elif pcr_interpretation["label"] == "Bearish (Call writing dominant)":
    pcr_score = -1

print(f"PCR OI:{pcr} ChgOI:{pcr_change_oi} Vol:{pcr_volume} OTM:{pcr_otm} "
      f"| {pcr_interpretation['label']} (pct:{pcr_interpretation['percentile']}, "
      f"z:{pcr_interpretation['z_score']}) | Trend: {pcr_trend} | PCR Score:{pcr_score}")


# ============================================================
# LEVEL 7 - FINAL DECISION: five independent GROUP scores, one per
# level-cluster, so no single level (e.g. option OI alone, like v5)
# can swing BUY/SELL by itself. A signal additionally needs at least
# 3-of-5 groups to agree in direction (confluence), not just a raw
# score threshold.
#
# NOTE: the exact thresholds below (group score bands, final_score
# cutoff, "3-of-5" confluence requirement) are reasonable starting
# defaults, NOT backtested values - tune them against your own data
# the same way you backtested the original 16-parameter framework.
# ============================================================

# --- Index-based Price+OI classification (kept from v5, now folded
# into the Regime/Context group - the REAL Level 2/5 Price+OI
# classification below runs on FUTURES, not this). ---
price_action = classify_price_action(nifty_change, pe_oi_change - ce_oi_change)

# --- LEVEL 2: Futures Price+OI classification (the real institutional
# signal - what v5 was missing entirely). ---
futures_price_action = classify_price_action(fut_change, fut_oi_change)

# --- SMC: Order Blocks / FVG / Supply-Demand zone score (Level 4 zone
# component - OB/FVG based, distinct from the resistance/support-
# strike and max-pain zone scores computed in the Level 4 block above). ---
structure_points = label_market_structure(smc_df)
order_blocks = detect_order_blocks(smc_df, smc_events, atr_value, lookback=50)
fvg_list = detect_fvg(smc_df, lookback=50)
nearest_demand, nearest_supply = nearest_supply_demand(nifty_ltp, order_blocks)
nearest_fvg_demand, nearest_fvg_supply = nearest_fvg_zones(nifty_ltp, fvg_list)

# UNIFIED zone (NEW): not OB-only anymore - combines OB + FVG + option
# OI support/resistance + prior swing + Equal Highs/Lows + confirmed
# liquidity sweep into one multi-source Demand/Supply zone. This
# REPLACES nearest_demand/nearest_supply as the zone used for the
# location filter, SMC trigger, message, and chart from here on -
# nearest_demand/nearest_supply (OB-only) are kept only as one of the
# inputs and for backward-compatible display.
# MAIN SUPPLY/DEMAND now comes from 1H + 30M only. 5M is the entry
# timeframe and does not redefine the higher-timeframe zone.
htf_demand_zone = build_mtf_supply_demand_zone(
    nifty_ltp, htf_zone_data, is_demand=True, atr_value=atr_value
)
htf_supply_zone = build_mtf_supply_demand_zone(
    nifty_ltp, htf_zone_data, is_demand=False, atr_value=atr_value
)

# Keep downstream variable names unchanged so existing chart/risk/message
# code uses the new HTF zones without adding a second competing zone engine.
unified_demand_zone = htf_demand_zone
unified_supply_zone = htf_supply_zone
print(f"HTF Demand Zone (1H+30M): {unified_demand_zone}")
print(f"HTF Supply Zone (1H+30M): {unified_supply_zone}")

# Raw snapshots captured BEFORE any multi-day mutation below, so what
# gets persisted for tomorrow's comparison is always today's actual
# zone - not one with an ever-growing "Prev-Day" source list and
# inflated strength stacking up day after day.
_raw_demand_zone_snapshot = dict(unified_demand_zone) if unified_demand_zone is not None else None
_raw_supply_zone_snapshot = dict(unified_supply_zone) if unified_supply_zone is not None else None

# ============================================================
# v6.14.5 MULTI-DAY ZONE MEMORY
#
# A 1H/30M Demand/Supply zone that only shows up on today's data is
# just today's noise until proven otherwise. A zone that ALSO existed
# on yesterday's 1H/30M chart, in roughly the same place, and is still
# being respected today, is the kind of zone institutions actually
# defend - that's what "sach me yehi zone bn rahi hai ya nahi" means
# in practice: does it survive a full session, not just this cycle.
#
# State keeps two things across restarts:
#   zone_track_date / zone_track_demand / zone_track_supply
#       -> the most recently computed zone, refreshed every cycle,
#          whatever day that was.
#   prev_day_zone_date / prev_day_demand_zone / prev_day_supply_zone
#       -> a snapshot that only gets rotated ONCE, the first cycle we
#          notice the calendar date has changed. This is "yesterday's
#          final zone" and stays fixed for the rest of today so every
#          cycle today is compared against the SAME prior session,
#          not a constantly moving target.
# ============================================================
today_ist_date = str((datetime.now() + timedelta(hours=5, minutes=30)).date())
_zone_track_date = state.get("zone_track_date")
_zone_track_demand = state.get("zone_track_demand")
_zone_track_supply = state.get("zone_track_supply")

prev_day_zone_date = state.get("prev_day_zone_date")
prev_day_demand_zone = state.get("prev_day_demand_zone")
prev_day_supply_zone = state.get("prev_day_supply_zone")

if _zone_track_date is not None and _zone_track_date != today_ist_date:
    # First cycle of a new day - freeze yesterday's last-known zone as
    # the reference for today's multi-day confluence check.
    prev_day_zone_date = _zone_track_date
    prev_day_demand_zone = _zone_track_demand
    prev_day_supply_zone = _zone_track_supply


def _zone_overlap(zone_a, zone_b, atr):
    if zone_a is None or zone_b is None:
        return False
    tol = max((atr or 0) * 0.3, 1)
    return (float(zone_a["top"]) + tol) >= float(zone_b["bottom"]) and \
           (float(zone_b["top"]) + tol) >= float(zone_a["bottom"])


demand_zone_multi_day = False
supply_zone_multi_day = False

if unified_demand_zone is not None and prev_day_demand_zone is not None:
    demand_zone_multi_day = _zone_overlap(unified_demand_zone, prev_day_demand_zone, atr_value)
    unified_demand_zone["multi_day_confirmed"] = demand_zone_multi_day
    if demand_zone_multi_day:
        unified_demand_zone["sources"] = unified_demand_zone["sources"] + [
            f"Prev-Day ({prev_day_zone_date}) Zone: "
            f"{round(prev_day_demand_zone['bottom'],1)}-{round(prev_day_demand_zone['top'],1)}"
        ]
elif unified_demand_zone is not None:
    unified_demand_zone["multi_day_confirmed"] = False

if unified_supply_zone is not None and prev_day_supply_zone is not None:
    supply_zone_multi_day = _zone_overlap(unified_supply_zone, prev_day_supply_zone, atr_value)
    unified_supply_zone["multi_day_confirmed"] = supply_zone_multi_day
    if supply_zone_multi_day:
        unified_supply_zone["sources"] = unified_supply_zone["sources"] + [
            f"Prev-Day ({prev_day_zone_date}) Zone: "
            f"{round(prev_day_supply_zone['bottom'],1)}-{round(prev_day_supply_zone['top'],1)}"
        ]
elif unified_supply_zone is not None:
    unified_supply_zone["multi_day_confirmed"] = False

print(
    f"Multi-day zone check vs {prev_day_zone_date} -> "
    f"Demand still valid today: {demand_zone_multi_day} | "
    f"Supply still valid today: {supply_zone_multi_day}"
)

# ============================================================
# v6.17 MULTI-DAY SUPPORT/RESISTANCE MEMORY
#
# Same idea as the zone memory above, but for the Level-4 OI-based
# Resistance(CE)/Support(PE) strikes: a strike that was already acting
# as resistance/support YESTERDAY, and is still roughly in the same
# place today, is a much stronger level than one that just showed up
# this cycle. Freezes yesterday's final resistance/support strike once
# per day (same "rotate on date change" pattern as the zone memory),
# then every cycle today checks whether today's strike is still close
# to it.
# ============================================================
_sr_track_date = state.get("sr_track_date")
_sr_track_resistance = state.get("sr_track_resistance")
_sr_track_support = state.get("sr_track_support")

prev_day_sr_date = state.get("prev_day_sr_date")
prev_day_resistance_strike = state.get("prev_day_resistance_strike")
prev_day_support_strike = state.get("prev_day_support_strike")

if _sr_track_date is not None and _sr_track_date != today_ist_date:
    prev_day_sr_date = _sr_track_date
    prev_day_resistance_strike = _sr_track_resistance
    prev_day_support_strike = _sr_track_support


def _level_overlap(level_a, level_b, atr):
    if level_a is None or level_b is None:
        return False
    tol = max((atr or 0) * 0.3, 50)  # 50pt floor ~= one Nifty strike gap
    return abs(float(level_a) - float(level_b)) <= tol


resistance_multi_day = _level_overlap(resistance_strike, prev_day_resistance_strike, atr_value)
support_multi_day = _level_overlap(support_strike, prev_day_support_strike, atr_value)

print(
    f"Multi-day S/R check vs {prev_day_sr_date} -> "
    f"Resistance still valid today: {resistance_multi_day} | "
    f"Support still valid today: {support_multi_day}"
)

_last_closed_candle = smc_df.iloc[-1] if smc_df is not None and len(smc_df) > 0 else None
zone_score = smc_zone_score(_last_closed_candle, nearest_demand, nearest_supply,
                             nearest_fvg_demand, nearest_fvg_supply, atr_value)

# --- SMC: Liquidity Sweeps / Stop Hunts (wick-based, body-close BOS/CHOCH
# above cannot see these - a sweep grabs stops with a wick then reverses) ---
liquidity_sweeps = detect_liquidity_sweeps(smc_df, lookback=50, wick_buffer_pct=0.02)
sweep_score = liquidity_sweep_score(liquidity_sweeps, smc_df, recency=5)

# --- LEVEL 3: Options aggregate OI component (no longer x2-dominant -
# that weight now belongs to Futures, see Group 1 below) ---
oi_diff = pe_oi_change - ce_oi_change
oi_magnitude_ref = max(abs(ce_oi_change), abs(pe_oi_change), 1)
if oi_diff > 0:
    oi_score = 2 if abs(oi_diff) > (0.5 * oi_magnitude_ref) else 1
elif oi_diff < 0:
    oi_score = -2 if abs(oi_diff) > (0.5 * oi_magnitude_ref) else -1
else:
    oi_score = 0

# --- Volume confirmation bonus (only counts if it AGREES with OI) ---
vol_diff = pe_vol_change - ce_vol_change
volume_bonus = 0
if oi_score > 0 and vol_diff > 0:
    volume_bonus = 1
elif oi_score < 0 and vol_diff < 0:
    volume_bonus = -1

# --- Price action / MTF minor components (Regime/Context group) ---
PRICE_ACTION_SCORE = {
    "LONG BUILD-UP": 1, "SHORT COVERING": 1,
    "SHORT BUILD-UP": -1, "LONG UNWINDING": -1,
    "NEUTRAL": 0,
}
price_action_score = PRICE_ACTION_SCORE.get(price_action, 0)
futures_action_score = PRICE_ACTION_SCORE.get(futures_price_action, 0)

# Midcap Nifty + Bank Nifty = confirmation/context only; neither can trigger a trade alone.
# v6.14 fix #11: require a meaningful move (not a sign-only flip on
# index noise) before BankNifty/Midcap contribute anything.
_midcap_pct = (midcap_change / midcap_price * 100) if midcap_price else 0
_banknifty_pct = (banknifty_change / banknifty_price * 100) if banknifty_price else 0
CORRELATED_INDEX_MIN_MOVE_PCT = 0.15
midcap_score = 1 if _midcap_pct > CORRELATED_INDEX_MIN_MOVE_PCT else (-1 if _midcap_pct < -CORRELATED_INDEX_MIN_MOVE_PCT else 0)
banknifty_score = 1 if _banknifty_pct > CORRELATED_INDEX_MIN_MOVE_PCT else (-1 if _banknifty_pct < -CORRELATED_INDEX_MIN_MOVE_PCT else 0)
# mtf_trend is context-only now - not scored, not a filter, just shown
# in the message (Level 6 section) per your instruction. mtf_score is
# kept only in case you want it back later; it's not used anywhere.
mtf_score = 1 if mtf_trend == "up" else (-1 if mtf_trend == "down" else 0)

# ============================================================
# VIX Analyzer (from vix_analyzer.py) - VIX judged on 3 axes, not
# just the raw number: absolute band (premium behaviour), historical
# percentile (is 16 "high" for THIS market's recent regime or not),
# and rate of change (spiking vs settling). Also derives a second,
# independent expected-move support/resistance band from VIX itself
# (distinct from the OI-based support/resistance computed earlier).
# ============================================================

VIX_PERCENTILE_LOOKBACK = 60      # recent 5m cycles compared against
VIX_TREND_LOOKBACK = 2            # readings compared for trend()
VIX_MIN_SIGNAL_CONFIDENCE = 0.5   # below this, signal doesn't count
VIX_MAX_HISTORY_LEN = 300         # rolling cap in state.json

_VIX_BAND_TABLE = [
    (0, 12, "CALM", "Option sellers ke liye kam margin / kam premium"),
    (12, 15, "NORMAL", "Balanced premium"),
    (15, 20, "ELEVATED", "Premium badhne lagte hain"),
    (20, 30, "HIGH", "Premium bahut badhenge - buyers risky, sellers ke liye bada premium"),
    (30, float("inf"), "EXTREME", "Premium explode ho sakte hain, dono taraf risk high"),
]


def classify_vix_band(vix):
    if vix is None:
        return "Unknown", "VIX unavailable"
    for low, high, band, note in _VIX_BAND_TABLE:
        if low <= vix < high:
            return band, note
    return "EXTREME", "Unclassified - data check karo"


def vix_expected_move(spot, vix):
    """VIX-implied 1-day expected move -> independent support/
    resistance band, separate from the option-OI-based one."""
    if spot is None or vix is None or spot <= 0 or vix < 0:
        return None
    daily_pct = vix / math.sqrt(252)
    move_pts = spot * (daily_pct / 100)
    return {
        "daily_pct": round(daily_pct, 2),
        "move_points": round(move_pts, 1),
        "support": round(spot - move_pts, 1),
        "resistance": round(spot + move_pts, 1),
    }


def vix_percentile_rank(vix, history, lookback=VIX_PERCENTILE_LOOKBACK):
    if vix is None:
        return None
    hist = [h for h in history[-lookback:] if h is not None]
    if len(hist) < 10:
        return None
    below = sum(1 for h in hist if h <= vix)
    return round(100 * below / len(hist), 1)


def vix_trend_direction(history, lookback=VIX_TREND_LOOKBACK):
    hist = [h for h in history[-lookback:] if h is not None]
    if len(hist) < 2:
        return "flat"
    if hist[-1] > hist[0]:
        return "up"
    if hist[-1] < hist[0]:
        return "down"
    return "flat"


def vix_generate_signal(htf_trend, vix_trend, percentile):
    """
    Base rules: trending + VIX up -> PUT bias | sideways + VIX down
    -> CALL bias. Everything else -> NEUTRAL. Confidence starts at
    0.5 and is only sharpened when the VIX percentile actually
    confirms the direction - a pure trend read alone never gets full
    confidence without that confirmation.
    """
    if htf_trend == "trending" and vix_trend == "up":
        direction = "PUT_BIAS"
    elif htf_trend == "sideways" and vix_trend == "down":
        direction = "CALL_BIAS"
    else:
        return "NEUTRAL", 0.0

    confidence = 0.5
    if percentile is not None:
        if direction == "PUT_BIAS" and percentile >= 80:
            confidence += 0.3
        elif direction == "CALL_BIAS" and percentile <= 20:
            confidence += 0.3
        else:
            confidence += 0.1
    return direction, min(confidence, 1.0)


vix_band, vix_premium_note = classify_vix_band(india_vix)
vix_move = vix_expected_move(nifty_ltp, india_vix)
vix_percentile = vix_percentile_rank(india_vix, prev_vix_history)
vix_trend = vix_trend_direction(prev_vix_history + [india_vix])
# htf_trend proxy: mtf_trend ("up"/"down") means BOS/CHOCH already
# confirmed a genuine structure break -> market is trending. mtf_trend
# is None -> no confirmed break yet -> ranging/sideways.
_htf_trend_proxy = "trending" if mtf_trend in ("up", "down") else "sideways"
vix_signal_direction, vix_signal_confidence = vix_generate_signal(
    _htf_trend_proxy, vix_trend, vix_percentile)

vix_history = (prev_vix_history + [india_vix])[-VIX_MAX_HISTORY_LEN:]

# PUT bias = bearish for the underlying -> negative score, CALL bias
# = bullish -> positive score. Only counts if confidence clears the
# minimum bar; a NEUTRAL or low-confidence read contributes 0.
vix_signal_score = 0
if vix_signal_confidence >= VIX_MIN_SIGNAL_CONFIDENCE:
    if vix_signal_direction == "PUT_BIAS":
        vix_signal_score = -1
    elif vix_signal_direction == "CALL_BIAS":
        vix_signal_score = 1

print(f"VIX Band:{vix_band} ({vix_premium_note}) | Percentile:{vix_percentile} | Trend:{vix_trend} "
      f"| Expected Move: +/-{vix_move['move_points'] if vix_move else 'N/A'} pts "
      f"(S:{vix_move['support'] if vix_move else 'N/A'} R:{vix_move['resistance'] if vix_move else 'N/A'}) "
      f"| Signal:{vix_signal_direction} (conf:{vix_signal_confidence:.2f}) | Score:{vix_signal_score}")

# ============================================================
# The 5 GROUP scores (Level 7)
# ============================================================

# Group 1 - LEVEL 2: Futures Institutional Positioning.
# v6.14 fix #10: the old x2 multiplier had no backtest/forward-test
# behind it and let futures alone outweigh 2 other full groups
# combined. Reset to x1 (FUTURES_WEIGHT below) - raise it later only
# once you've logged enough cycles to justify a specific number.
FUTURES_WEIGHT = 1
futures_group_score = (futures_action_score * FUTURES_WEIGHT) + fii_fut_score

# Group 2 - LEVEL 3: Option Chain Positioning (aggregate OI +
# volume confirmation + near-ATM Call/Put writing pressure).
options_group_score = oi_score + volume_bonus + writing_score + pcr_score

# Group 3 - LEVEL 4: Institutional Zones (OB/FVG demand-supply +
# support/resistance strike proximity + max pain gravitational pull).
zones_group_score = zone_score + sr_score + maxpain_score

# Group 4 - LEVEL 6: SMC structure (BOS/CHOCH trend + liquidity sweeps).
# Liquidity Map score gets 2x weight vs the plain sweep_score above -
# it only fires when the FULL chain confirms (Sweep+Rejection+
# Displacement+BOS/CHOCH+Volume/OI), so it's a much stronger signal
# than a bare wick-and-reject. Weight is a tunable default, same as
# the other group weights - not backtested.
smc_group_score = sweep_score + (liquidity_score * 2)

# Group 5 - LEVEL 1/5: Regime & Context (opening range + global cues +
# index-level price/OI classification - all minor, contextual nudges).
context_group_score = orb_score + price_action_score + midcap_score + banknifty_score + vix_signal_score

# v6.14 fix #12: context is a tie-breaker, not a 6th structural vote.
# Half-weighted into final_score, and deliberately left OUT of the
# confluence tally below (CORE_GROUPS only) so ORB+BankNifty+Midcap
# alignment alone can never count as one of the "3 groups agree" votes
# that actual price structure (Zones/SMC) has to earn on its own.
CONTEXT_WEIGHT = 0.5
final_score = (
    futures_group_score + options_group_score + zones_group_score
    + smc_group_score + (context_group_score * CONTEXT_WEIGHT)
)

CORE_GROUPS = {
    "Futures": futures_group_score,
    "Options Chain": options_group_score,
    "Zones": zones_group_score,
    "SMC": smc_group_score,
}
group_scores = dict(CORE_GROUPS, **{"Regime/Context (context-only, not voted)": context_group_score})
bull_groups = sum(1 for v in CORE_GROUPS.values() if v > 0)
bear_groups = sum(1 for v in CORE_GROUPS.values() if v < 0)

print(f"Group Scores -> {group_scores} | Bull groups:{bull_groups} Bear groups:{bear_groups} "
      f"=> Composite:{final_score}")


# ============================================================
# PRIMARY STRUCTURAL ENTRY ENGINE
#
# Decision chain:
#   LOCATION -> LIQUIDITY -> SWEEP/REJECTION -> DISPLACEMENT
#   -> BOS/CHOCH -> RETEST -> ENTRY
#
# Futures/OI/PCR/Volume/VWAP/Global cues are confirmation/context only.
# They can increase/decrease confidence, but they CANNOT manufacture a
# BUY/SELL when the primary price structure is absent.
#
# v6.15: Supply/Demand is contextual/location information. It is not a
# directional shortcut and does not block a genuine market-behaviour read.
# Sweep/retest remains a separate structural reversal path.
# ============================================================
ZONE_PROXIMITY_TOLERANCE = 0.3 * atr_value if atr_value and atr_value > 0 else 0.0


def _price_at_demand(low_price, close_price, zone):
    if zone is None:
        return False
    return (
        float(low_price) <= float(zone["top"]) + ZONE_PROXIMITY_TOLERANCE
        and float(close_price) >= float(zone["bottom"]) - ZONE_PROXIMITY_TOLERANCE
    )


def _price_at_supply(high_price, close_price, zone):
    if zone is None:
        return False
    return (
        float(high_price) >= float(zone["bottom"]) - ZONE_PROXIMITY_TOLERANCE
        and float(close_price) <= float(zone["top"]) + ZONE_PROXIMITY_TOLERANCE
    )


primary_setup = "NEUTRAL"
primary_setup_reason = "No complete structural setup"
primary_sweep = None
primary_bos = None
primary_retest = False
primary_continuation = False

# v6.14.3: continuation entry path. A sweep is required for a reversal
# setup, NOT for a clean trend continuation. This keeps BUY and SELL
# symmetric and prevents a strong one-way move from being ignored just
# because a fresh liquidity sweep never occurred.
def _continuation_setup(df, events, entry_df, direction, atr, zone_demand, zone_supply):
    if df is None or len(df) < 4 or atr is None or atr <= 0:
        return False, None, ""

    last = df.iloc[-1]
    prev = df.iloc[-2]
    bull = float(last["close"]) > float(last["open"])
    bear = float(last["close"]) < float(last["open"])
    displacement = float(last["high"] - last["low"]) >= 0.8 * atr

    wanted = "Bullish" if direction == "BUY" else "Bearish"
    recent_events = [
        ev for ev in events
        if ev[0] <= last["time"] and wanted in ev[1]
    ][-3:]
    if not recent_events:
        return False, None, ""

    # Keep the structural break fresh; an old BOS must not create a new
    # continuation entry many candles later.
    times = list(df["time"])
    try:
        bos_pos = times.index(recent_events[-1][0])
    except ValueError:
        return False, None, ""
    if len(times) - 1 - bos_pos > 8:
        return False, None, ""

    if direction == "SELL":
        # Bearish continuation: structure already broke down and price is
        # still accepting below the prior candle/structure, rather than
        # requiring another sweep + retest.
        continuation_price = float(last["close"]) < float(prev["close"]) or float(last["close"]) < float(prev["low"])
        candle_ok = bear or displacement
        five_ok = False
        if entry_df is not None and not entry_df.empty:
            c5 = entry_df.tail(3)
            bear_count = int((c5["close"] < c5["open"]).sum())
            five_ok = bear_count >= 2 or float(c5.iloc[-1]["close"]) < float(c5.iloc[-2]["low"])
        if candle_ok and continuation_price and five_ok:
            return True, recent_events[-1], "Bearish BOS/CHOCH -> 5M continuation -> 5M bearish confirmation"
    else:
        continuation_price = float(last["close"]) > float(prev["close"]) or float(last["close"]) > float(prev["high"])
        candle_ok = bull or displacement
        five_ok = False
        if entry_df is not None and not entry_df.empty:
            c5 = entry_df.tail(3)
            bull_count = int((c5["close"] > c5["open"]).sum())
            five_ok = bull_count >= 2 or float(c5.iloc[-1]["close"]) > float(c5.iloc[-2]["high"])
        if candle_ok and continuation_price and five_ok:
            return True, recent_events[-1], "Bullish BOS/CHOCH -> 5M continuation -> 5M bullish confirmation"

    return False, None, ""

# v6.14.4 EARLY ENTRY PATH: do not wait for the next 5M candle to
# confirm a move that is already starting on 5M. 5M structure remains
# the context; the FIRST CLOSED 5M break is allowed to trigger the entry.
# This uses only candles already closed at decision time (no look-ahead).
def _early_5m_trigger(entry_df, structure_points, atr, direction, zone_demand, zone_supply):
    if entry_df is None or len(entry_df) < 2 or not structure_points or atr is None or atr <= 0:
        return False, None, ""

    # Established 5M structure: last confirmed high + low must agree.
    highs = [x for x in structure_points if x["kind"] == "high"]
    lows = [x for x in structure_points if x["kind"] == "low"]
    if not highs or not lows:
        return False, None, ""
    last_high = highs[-1]["label"]
    last_low = lows[-1]["label"]

    if direction == "SELL":
        structure_ok = last_high == "LH" and last_low == "LL"
    else:
        structure_ok = last_high == "HH" and last_low == "HL"
    if not structure_ok:
        return False, None, ""

    c = entry_df.iloc[-1]
    prev = entry_df.iloc[-2]
    o, h, l, cl = map(float, (c["open"], c["high"], c["low"], c["close"]))
    ph, pl = float(prev["high"]), float(prev["low"])
    rng = h - l

    # v6.16: 1H/30M HTF zone is NO LONGER a mandatory gate here (per
    # user request) - it used to hard-block this early path if price
    # wasn't sitting at the HTF Demand/Supply zone. Now it is only
    # computed for the reason text / confirmation display; it can no
    # longer return False on its own or stop a BUY/SELL from firing.
    if direction == "SELL":
        at_location = _price_at_supply(h, cl, zone_supply)
    else:
        at_location = _price_at_demand(l, cl, zone_demand)
    zone_note = "1H/30M zone confirmed" if at_location else "1H/30M zone not confirmed - context only"

    # First decisive 5M break. Much earlier than waiting for a new 5M
    # BOS/retest, while still requiring a real candle body and displacement.
    if direction == "SELL":
        body_ok = cl < o
        break_ok = cl < pl
    else:
        body_ok = cl > o
        break_ok = cl > ph
    displacement_ok = rng >= 0.25 * atr

    if body_ok and break_ok and displacement_ok:
        return True, (c["time"], f"EARLY BOS ({'Bearish' if direction == 'SELL' else 'Bullish'})", cl), (
            f"EARLY SELL: 5M LH+LL -> first 5M downside break ({zone_note})"
            if direction == "SELL" else
            f"EARLY BUY: 5M HH+HL -> first 5M upside break ({zone_note})"
        )
    return False, None, ""

# IMPORTANT: early path runs BEFORE the old 5M-continuation confirmation.
# If the first 5M break is already visible, do not wait for another 5M candle.
if primary_setup == "NEUTRAL" and atr_value and atr_value > 0:
    for _direction in ("SELL", "BUY"):
        _ok, _trigger, _reason = _early_5m_trigger(
            entry_5m_df, structure_points, atr_value, _direction,
            unified_demand_zone, unified_supply_zone,
        )
        if _ok:
            primary_setup = _direction
            primary_setup_reason = _reason
            primary_bos = _trigger
            primary_continuation = True
            primary_retest = False
            break

# ============================================================
# MARKET-BEHAVIOUR ENGINE (v6.15)
#
# This is an interpretation layer, not a new indicator. It combines the
# EXISTING price structure, 5M reaction, VWAP/session position and the
# existing institutional/OI/SMC groups into one current state:
#   BUYING_CONTROL / SELLING_CONTROL / BALANCED / TRANSITION
#
# Supply/Demand remains location/context. A zone by itself never creates
# a BUY/SELL. Liquidity sweep remains a separate reversal path.
# ============================================================
def _market_behaviour_state(smc_df, entry_df, structure_points, atr,
                            vwap, session_open, core_groups):
    """Read CURRENT market control from existing modules, without waiting
    for a full sweep->BOS->retest chain.  This is a state/interpretation
    layer, not a new indicator.

    The important distinction is: a move can become controlled before a
    fresh 5M BOS/CHOCH is confirmed.  We therefore use independent
    existing evidence (price acceptance, futures, options, zones, SMC,
    5M pressure and global context) as evidence of control.
    """
    if atr is None or atr <= 0 or smc_df is None or len(smc_df) < 2:
        return "BALANCED", 0, "Insufficient closed-candle data", 0

    # Confirmed 5M structure is confirmation/context. It must not be the
    # starting gate for recognising a move that is already developing.
    highs = [x["label"] for x in structure_points if x["kind"] == "high"] if structure_points else []
    lows = [x["label"] for x in structure_points if x["kind"] == "low"] if structure_points else []
    structure_score = 0
    if highs and lows:
        if highs[-1] == "HH" and lows[-1] == "HL":
            structure_score = 2
        elif highs[-1] == "LH" and lows[-1] == "LL":
            structure_score = -2

    # 5M is pressure confirmation, NOT a mechanical breakout trigger.
    c5 = entry_df.tail(3) if entry_df is not None and len(entry_df) >= 3 else pd.DataFrame()
    pressure_score = 0
    if not c5.empty:
        signed_bodies = float((c5["close"] - c5["open"]).astype(float).sum())
        bull_count = int((c5["close"] > c5["open"]).sum())
        bear_count = int((c5["close"] < c5["open"]).sum())
        net_move = float(c5.iloc[-1]["close"] - c5.iloc[0]["open"])
        move_strength = abs(net_move) / atr
        if move_strength >= 0.20:
            if signed_bodies > 0 and bull_count >= 2:
                pressure_score = 2 if move_strength >= 0.45 else 1
            elif signed_bodies < 0 and bear_count >= 2:
                pressure_score = -2 if move_strength >= 0.45 else -1

    # Price acceptance: strong when price is on the same side of BOTH
    # VWAP and session open.
    price_score = 0
    ltp = float(smc_df.iloc[-1]["close"])
    if vwap is not None and session_open is not None:
        if ltp > float(vwap) and ltp > float(session_open):
            price_score = 1
        elif ltp < float(vwap) and ltp < float(session_open):
            price_score = -1

    # Build independent evidence votes from EXISTING modules.  These are
    # signs, not arbitrary extra indicators.  A single module cannot
    # manufacture a direction by itself.
    votes = {"BUY": [], "SELL": []}

    if structure_score > 0:
        votes["BUY"].append("5M structure")
    elif structure_score < 0:
        votes["SELL"].append("5M structure")

    if pressure_score > 0:
        votes["BUY"].append("5M pressure")
    elif pressure_score < 0:
        votes["SELL"].append("5M pressure")

    if price_score > 0:
        votes["BUY"].append("VWAP/session acceptance")
    elif price_score < 0:
        votes["SELL"].append("VWAP/session acceptance")

    # Futures gets its own explicit evidence because it is the strongest
    # existing institutional price+OI module.
    if futures_group_score > 0 or futures_price_action in ("LONG BUILD-UP", "SHORT COVERING"):
        votes["BUY"].append("futures")
    elif futures_group_score < 0 or futures_price_action in ("SHORT BUILD-UP", "LONG UNWINDING"):
        votes["SELL"].append("futures")

    if options_group_score > 0:
        votes["BUY"].append("options")
    elif options_group_score < 0:
        votes["SELL"].append("options")

    if zones_group_score > 0:
        votes["BUY"].append("zones")
    elif zones_group_score < 0:
        votes["SELL"].append("zones")

    if smc_group_score > 0:
        votes["BUY"].append("SMC")
    elif smc_group_score < 0:
        votes["SELL"].append("SMC")

    # Global cues remain weak context; they can help break a tie but are
    # not required for a signal.
    if global_score > 0:
        votes["BUY"].append("global context")
    elif global_score < 0:
        votes["SELL"].append("global context")

    buy_n = len(votes["BUY"])
    sell_n = len(votes["SELL"])

    # Three independent modules can establish developing control.  Four
    # or more is stronger.  Opposite evidence must not be simultaneously
    # strong.  This is deliberately earlier than waiting for a confirmed
    # 5M BOS/retest.
    if sell_n >= 3 and sell_n >= buy_n + 2:
        score = sell_n - buy_n
        return "SELLING_CONTROL", score, (
            f"sellers controlling: {sell_n} existing signals agree "
            f"({', '.join(votes['SELL'])}); opposite={buy_n}"
        ), structure_score

    if buy_n >= 3 and buy_n >= sell_n + 2:
        score = buy_n - sell_n
        return "BUYING_CONTROL", score, (
            f"buyers controlling: {buy_n} existing signals agree "
            f"({', '.join(votes['BUY'])}); opposite={sell_n}"
        ), structure_score

    if buy_n == 0 and sell_n == 0:
        return "BALANCED", 0, "No side has meaningful existing evidence", structure_score

    return "TRANSITION", buy_n - sell_n, (
        f"control not yet decisive: BUY evidence={buy_n} "
        f"({', '.join(votes['BUY']) or 'none'}), SELL evidence={sell_n} "
        f"({', '.join(votes['SELL']) or 'none'})"
    ), structure_score

market_behaviour, behaviour_score, behaviour_reason, structure_score = _market_behaviour_state(
    smc_df, entry_5m_df, structure_points, atr_value, vwap_value, session_open, CORE_GROUPS
)
print(f"MARKET BEHAVIOUR -> {market_behaviour} | score:{behaviour_score} | {behaviour_reason}")

# Behaviour can create a candidate when multiple independent EXISTING
# signals agree. It does NOT use Supply/Demand as a directional shortcut.
#
# v6.16 STATE/HYSTERESIS: do not turn a still-valid directional move into
# NEUTRAL merely because one cycle's 5M pressure/SMC trigger went quiet.
# The previous state is retained only while the current evidence has NOT
# flipped to the opposite side. This prevents the exact SELL->NEUTRAL->SELL
# churn seen when a move is already underway.
if primary_setup == "NEUTRAL" and not atr_is_fallback:
    if market_behaviour == "BUYING_CONTROL":
        primary_setup = "BUY"
        primary_setup_reason = "MARKET BEHAVIOUR: " + behaviour_reason
        primary_continuation = True
        primary_retest = False
    elif market_behaviour == "SELLING_CONTROL":
        primary_setup = "SELL"
        primary_setup_reason = "MARKET BEHAVIOUR: " + behaviour_reason
        primary_continuation = True
        primary_retest = False
    elif prev_market_behaviour == "SELLING_CONTROL":
        # Keep SELL only if the current market has not flipped bullish:
        # price is not above both VWAP/open, futures are not bullish, and
        # 5M structure is not bullish.
        _sell_state_valid = (
            not (vwap_value is not None and session_open is not None
                 and nifty_ltp > float(vwap_value) and nifty_ltp > float(session_open))
            and futures_group_score <= 0
            and structure_score <= 0
        )
        if _sell_state_valid:
            primary_setup = "SELL"
            primary_setup_reason = (
                "PERSISTENT SELLING CONTROL: previous selling state remains valid; "
                "no bullish invalidation in current closed data"
            )
            primary_continuation = True
            primary_retest = False
    elif prev_market_behaviour == "BUYING_CONTROL":
        _buy_state_valid = (
            not (vwap_value is not None and session_open is not None
                 and nifty_ltp < float(vwap_value) and nifty_ltp < float(session_open))
            and futures_group_score >= 0
            and structure_score >= 0
        )
        if _buy_state_valid:
            primary_setup = "BUY"
            primary_setup_reason = (
                "PERSISTENT BUYING CONTROL: previous buying state remains valid; "
                "no bearish invalidation in current closed data"
            )
            primary_continuation = True
            primary_retest = False

if primary_setup == "NEUTRAL" and len(smc_df) >= 3 and atr_value and atr_value > 0 and confirmed_sweeps:
    _last = smc_df.iloc[-1]
    _last_time = _last["time"]
    _last_bull = float(_last["close"]) > float(_last["open"])
    _last_bear = float(_last["close"]) < float(_last["open"])
    _last_range = float(_last["high"] - _last["low"])
    _last_displacement = _last_range >= 0.8 * atr_value

    # A confirmed sweep already means: liquidity was taken and price
    # rejected/reclaimed the level. Pick the freshest structurally
    # confirmed sweep that is still relevant to the current candle.
    _ordered_confirmed = sorted(confirmed_sweeps, key=lambda z: z["time"])
    _recent_confirmed = [
        x for x in _ordered_confirmed
        if x["time"] <= _last_time
    ][-5:]

    # A sweep is only actionable while it is still fresh.  Do not let an
    # old historical sweep manufacture a new entry many candles later.
    _sweep_times = list(smc_df["time"])
    _last_pos = len(_sweep_times) - 1

    for _sweep in reversed(_recent_confirmed):
        try:
            _sweep_pos = _sweep_times.index(_sweep["time"])
        except ValueError:
            continue
        if (_last_pos - _sweep_pos) > 8:
            continue
        _direction = "BUY" if _sweep["type"] == "bullish_sweep" else "SELL"
        _matching_events = [
            (ev_time, ev_label, ev_price)
            for ev_time, ev_label, ev_price in smc_events
            if ev_time > _sweep["time"] and ev_time <= _last_time
            and ((_direction == "BUY" and "Bullish" in ev_label)
                 or (_direction == "SELL" and "Bearish" in ev_label))
        ]
        if not _matching_events:
            continue

        _bos = _matching_events[-1]
        _bos_time = _bos[0]
        _level = float(_sweep["level"])

        # Retest must occur after the confirmed BOS/CHOCH candle.
        if _last_time <= _bos_time:
            continue

        if _direction == "BUY":
            # v6.16: 1H/30M HTF zone is confirmation/display only now
            # (per user request) - it no longer has to match for a
            # retest to count. Only the actual liquidity-level retest
            # gates entry; _zone_retest is kept purely for the reason
            # text so you can see whether the HTF zone also agreed.
            _zone_retest = (
                unified_demand_zone is not None
                and float(_last["low"]) <= float(unified_demand_zone["top"])
                and float(_last["close"]) >= float(unified_demand_zone["bottom"])
            )
            _liquidity_retest = (
                float(_last["low"]) <= _level
                and float(_last["close"]) > _level
            )
            primary_retest = bool(_liquidity_retest)

            if primary_retest and (_last_bull or _last_displacement):
                # 5M is an entry refinement/confirmation layer. It never
                # cancels a valid 5M structural setup; it only tells us
                # whether the 5M candle is already reacting in the same way.
                _5m_ok = False
                if not entry_5m_df.empty:
                    _c5 = entry_5m_df.iloc[-1]
                    _5m_ok = float(_c5["close"]) > float(_c5["open"])
                primary_setup = "BUY"
                primary_setup_reason = (
                    "Demand/SSL sweep -> rejection -> displacement/BOS -> bullish retest"
                    + (" -> 5M bullish confirmation" if _5m_ok else " -> 5M confirmation pending")
                    + (" (1H/30M zone confirmed)" if _zone_retest else " (1H/30M zone not confirmed - context only)")
                )
                primary_sweep = _sweep
                primary_bos = _bos
                primary_continuation = False
                break

        else:
            # v6.16: same as BUY branch above - HTF zone no longer gates
            # this retest, it is shown in the reason text only.
            _zone_retest = (
                unified_supply_zone is not None
                and float(_last["high"]) >= float(unified_supply_zone["bottom"])
                and float(_last["close"]) <= float(unified_supply_zone["top"])
            )
            _liquidity_retest = (
                float(_last["high"]) >= _level
                and float(_last["close"]) < _level
            )
            primary_retest = bool(_liquidity_retest)

            if primary_retest and (_last_bear or _last_displacement):
                # 5M is an entry refinement/confirmation layer. It never
                # cancels a valid 5M structural setup; it only tells us
                # whether the 5M candle is already reacting in the same way.
                _5m_ok = False
                if not entry_5m_df.empty:
                    _c5 = entry_5m_df.iloc[-1]
                    _5m_ok = float(_c5["close"]) < float(_c5["open"])
                primary_setup = "SELL"
                primary_setup_reason = (
                    "Supply/BSL sweep -> rejection -> displacement/BOS -> bearish retest"
                    + (" -> 5M bearish confirmation" if _5m_ok else " -> 5M confirmation pending")
                    + (" (1H/30M zone confirmed)" if _zone_retest else " (1H/30M zone not confirmed - context only)")
                )
                primary_sweep = _sweep
                primary_bos = _bos
                primary_continuation = False
                break

# v6.14.3 continuation path: if no reversal setup was found, allow a
# clean already-established trend to produce an entry without demanding a
# new liquidity sweep. This is deliberately mirrored for BUY and SELL.
if primary_setup == "NEUTRAL" and len(smc_df) >= 4 and atr_value and atr_value > 0:
    for _direction in ("SELL", "BUY"):
        _ok, _bos, _reason = _continuation_setup(
            smc_df, smc_events, entry_5m_df, _direction, atr_value,
            unified_demand_zone, unified_supply_zone,
        )
        if _ok:
            primary_setup = _direction
            primary_setup_reason = _reason
            primary_bos = _bos
            primary_continuation = True
            primary_retest = False
            break

# Keep smc_trigger as a display/diagnostic value, but it is no longer a
# veto-driven decision engine. The PRIMARY STRUCTURAL setup above owns
# the direction; secondary groups only confirm it.
smc_trigger = primary_setup
structural_override_veto = "NONE"
if primary_setup in ("BUY", "SELL"):
    structural_override_veto = primary_setup

print(
    f"PRIMARY STRUCTURE -> {primary_setup} | {primary_setup_reason}"
    + (f" | Sweep:{primary_sweep.get('label', primary_sweep.get('type'))}"
       f" | BOS/CHOCH:{primary_bos[1]} | Retest:{primary_retest}"
       if primary_sweep is not None and primary_bos is not None else "")
)

# ============================================================
# FINAL SIGNAL DECISION — STRUCTURE FIRST
#
# IMPORTANT: composite score and group confluence are NOT BUY/SELL
# gates anymore. They are confirmation/confidence information only.
#
# BUY requires the actual structural chain to exist.
# SELL requires the actual structural chain to exist.
# No complete chain = NEUTRAL, even if OI/PCR/Futures/Context produce
# a very large positive/negative composite score.
# ============================================================

price_above_vwap_and_open = (
    vwap_value is not None and session_open is not None
    and nifty_ltp > vwap_value and nifty_ltp > session_open
)
price_below_vwap_and_open = (
    vwap_value is not None and session_open is not None
    and nifty_ltp < vwap_value and nifty_ltp < session_open
)

# Location is descriptive/confirmation only here - it does NOT gate
# BUY/SELL (see v6.16 note above the entry-engine functions).
near_demand_zone = (
    unified_demand_zone is not None
    and (nifty_ltp - unified_demand_zone["top"]) <= ZONE_PROXIMITY_TOLERANCE
)
near_supply_zone = (
    unified_supply_zone is not None
    and (unified_supply_zone["bottom"] - nifty_ltp) <= ZONE_PROXIMITY_TOLERANCE
)

# ============================================================
# v6.16: Supply/Demand CROSS-CHECK (confirmation only, per user
# request - NOT used anywhere in the Buy/Sell decision).
#
# There are two independent ways this bot reads Supply/Demand:
#   1) OI DATA based  - resistance_strike/support_strike, from the
#      option chain's Change-in-OI (already used in sr_score, unchanged).
#   2) 1H/30M CHART based - unified_demand_zone/unified_supply_zone,
#      from Order Blocks/FVG on the 1H+30M candles (also unchanged).
# This block just checks whether the two AGREE (the OI strike falls
# inside/near the HTF zone) and shows that as a confirmation label in
# the Telegram message. It does not feed any score and does not block
# or trigger any BUY/SELL - it's purely "is this really a genuine
# zone, confirmed from a second, independent source".
# ============================================================
sd_cross_check_tolerance = ZONE_PROXIMITY_TOLERANCE

sd_demand_confirmed = (
    support_strike is not None
    and unified_demand_zone is not None
    and (unified_demand_zone["bottom"] - sd_cross_check_tolerance)
        <= support_strike <=
        (unified_demand_zone["top"] + sd_cross_check_tolerance)
)
sd_supply_confirmed = (
    resistance_strike is not None
    and unified_supply_zone is not None
    and (unified_supply_zone["bottom"] - sd_cross_check_tolerance)
        <= resistance_strike <=
        (unified_supply_zone["top"] + sd_cross_check_tolerance)
)

def _sd_cross_check_label(oi_level, htf_zone, confirmed):
    if oi_level is None or htf_zone is None:
        return "N/A (missing OI level or 1H/30M zone)"
    return (
        f"OI {oi_level} vs 1H/30M {round(htf_zone['bottom'],1)}-{round(htf_zone['top'],1)} -> "
        + ("CONFIRMED (both agree)" if confirmed else "NOT confirmed (sources disagree)")
    )

sd_demand_cross_check_text = _sd_cross_check_label(support_strike, unified_demand_zone, sd_demand_confirmed)
sd_supply_cross_check_text = _sd_cross_check_label(resistance_strike, unified_supply_zone, sd_supply_confirmed)

# Candidate direction comes from the validated primary structure OR the
# independent market-behaviour engine. The 1:2 RR check is still performed
# after structural SL/Target are calculated.
upside_walls = [lvl for lvl in [
    unified_supply_zone["bottom"] if unified_supply_zone is not None else None,
    resistance_strike,
] if lvl is not None and lvl > nifty_ltp]
buy_room = (min(upside_walls) - nifty_ltp) if upside_walls else None

downside_walls = [lvl for lvl in [
    unified_demand_zone["top"] if unified_demand_zone is not None else None,
    support_strike,
] if lvl is not None and lvl < nifty_ltp]
sell_room = (nifty_ltp - max(downside_walls)) if downside_walls else None

if atr_is_fallback:
    final_signal = "NEUTRAL"
elif primary_setup in ("BUY", "SELL"):
    final_signal = primary_setup
else:
    final_signal = "NEUTRAL"

raw_signal = final_signal

# ============================================================
# RISK MANAGEMENT: fixed 1:2 Risk/Reward
# Entry = ACTUAL STRUCTURAL TRIGGER price, NOT a later live LTP.
# For a 5M-confirmed setup, use the latest 5M confirmation candle close.
# Otherwise use the 5M trigger candle close (BOS/CHOCH/retest candle).
# This prevents a delayed Telegram/API cycle from creating an entry at a
# price that the trigger candle never traded.
# Target = exactly 2R. No automatic broker order is placed/exited.
# ============================================================

def _get_structural_entry_price(direction):
    # Prefer the latest 5M confirmation candle when it agrees with the
    # primary setup. Its close is a price actually traded by that candle.
    if entry_5m_df is not None and not entry_5m_df.empty:
        _c5 = entry_5m_df.iloc[-1]
        _c5_close = float(_c5["close"])
        _c5_bull = _c5_close > float(_c5["open"])
        _c5_bear = _c5_close < float(_c5["open"])
        if (direction == "BUY" and _c5_bull) or (direction == "SELL" and _c5_bear):
            return round(_c5_close, 1), "5M confirmation candle close"

    # Behaviour candidate: entry is the latest CLOSED 5M candle close.
    # This is an observed price, not a predicted future level.
    if primary_continuation and primary_bos is None and entry_5m_df is not None and not entry_5m_df.empty:
        _c5 = entry_5m_df.iloc[-1]
        return round(float(_c5["close"]), 1), "latest closed 5M behaviour candle close"

    # Fallback: the 5M structural trigger candle.
    if primary_bos is not None:
        _bos_time = primary_bos[0]
        _rows = smc_df[smc_df["time"] == _bos_time]
        if not _rows.empty:
            return round(float(_rows.iloc[-1]["close"]), 1), "5M BOS/CHOCH candle close"

    # Final fallback only when no trigger candle can be located.
    # This keeps the script operational but marks it clearly as fallback.
    return round(float(nifty_ltp), 1), "live LTP fallback"

entry_price = round(nifty_ltp, 1)
entry_price_source = "live LTP fallback"
if final_signal in ("BUY", "SELL"):
    entry_price, entry_price_source = _get_structural_entry_price(final_signal)
print(f"ENTRY PRICE -> {entry_price} | Source: {entry_price_source}")
RR_RATIO = 2.0

# ============================================================
# STALENESS GUARD (v6.14.5 fix): confirm_sweep() now allows up to
# `confirm_window=8` 5M candles between the sweep and its BOS/CHOCH
# confirmation. That is fine for validating the setup, but it also
# means the structural trigger candle (whose CLOSE we use as
# entry_price) can be up to ~2 hours old by the time this cycle runs
# and a Telegram message goes out. If live price has already run well
# past that trigger candle in the SAME direction, the "move" is
# already done and sending a fresh BUY/SELL now (still quoting the old
# trigger price) is exactly the "message after the move already
# happened" problem. Reject the signal in that case instead of sending
# a stale entry.
# ============================================================
MAX_ENTRY_STALENESS = 0.6 * atr_value if atr_value and atr_value > 0 else None
entry_staleness_reject = False
if final_signal in ("BUY", "SELL") and MAX_ENTRY_STALENESS is not None:
    _drift = (nifty_ltp - entry_price) if final_signal == "BUY" else (entry_price - nifty_ltp)
    # _drift > 0 means price has already moved further in the signal's
    # direction since the trigger candle closed - i.e. the move is
    # already underway/done, not fresh.
    if _drift > MAX_ENTRY_STALENESS:
        entry_staleness_reject = True
        print(
            f"STALENESS FILTER -> NEUTRAL | Trigger price {entry_price} but LTP {nifty_ltp} "
            f"already drifted {round(_drift, 1)} pts (max allowed {round(MAX_ENTRY_STALENESS, 1)}) "
            f"- move already happened, signal dropped."
        )
        final_signal = "NEUTRAL"

stop_loss = None
target = None
risk_points = None
reward_points = None
actual_rr = None
rr_valid = False
rr_reject_reason = None

if final_signal == "BUY":
    # For a bullish sweep, the sweep wick and Demand zone are the actual
    # invalidation structure. Stop goes below the deeper structural point.
    _sl_candidates = [
        unified_demand_zone["bottom"] if unified_demand_zone is not None else None,
        primary_sweep.get("wick") if primary_sweep is not None else None,
        (float(primary_bos[2]) if primary_continuation and primary_bos is not None else None),
    ]
    if primary_continuation and not any(x is not None and float(x) < entry_price for x in _sl_candidates):
        # Continuation BUY has no sweep wick; use the nearest recent 5M
        # swing low as the structural invalidation.
        _recent_lows = smc_df.loc[smc_df["swing_low"] == True, "low"] if "swing_low" in smc_df.columns else pd.Series(dtype=float)
        if not _recent_lows.empty:
            _sl_candidates.append(float(_recent_lows.iloc[-1]))
    _sl_candidates = [float(x) for x in _sl_candidates if x is not None and float(x) < entry_price]

    if _sl_candidates:
        # v6.17 CORRECTION: was min() - which picks the FARTHEST candidate
        # below entry (e.g. a multi-day Demand zone bottom hundreds of pts
        # away) instead of the nearest real invalidation (usually the sweep
        # wick). That produced absurd risk (500+ pts on a ~13pt ATR
        # instrument) and a 2R target that could never realistically be
        # reached - confusing the RR-reject message rather than genuinely
        # sizing the trade. Nearest valid structural point = max() of the
        # below-entry candidates.
        stop_loss = round(max(_sl_candidates), 1)
        risk_points = round(entry_price - stop_loss, 1)
        if risk_points > 0:
            reward_points = round(risk_points * RR_RATIO, 1)
            target = round(entry_price + reward_points, 1)

            # The 2R target must have clear room before the nearest opposing
            # structural wall. If a wall is inside 2R, skip the trade instead
            # of moving the target or weakening the RR requirement.
            _opposing_wall = min(upside_walls) if upside_walls else None
            if _opposing_wall is None or target <= float(_opposing_wall):
                rr_valid = True
            else:
                rr_reject_reason = f"2R target {target} is beyond opposing wall {_opposing_wall}"
    else:
        rr_reject_reason = "No valid bullish structural invalidation level"

elif final_signal == "SELL":
    # For a bearish sweep, the sweep wick and Supply zone are the actual
    # invalidation structure. Stop goes above the higher structural point.
    _sl_candidates = [
        unified_supply_zone["top"] if unified_supply_zone is not None else None,
        primary_sweep.get("wick") if primary_sweep is not None else None,
        (float(primary_bos[2]) if primary_continuation and primary_bos is not None else None),
    ]
    if primary_continuation and not any(x is not None and float(x) > entry_price for x in _sl_candidates):
        # Continuation SELL has no sweep wick; use the nearest recent 5M
        # swing high as the structural invalidation.
        _recent_highs = smc_df.loc[smc_df["swing_high"] == True, "high"] if "swing_high" in smc_df.columns else pd.Series(dtype=float)
        if not _recent_highs.empty:
            _sl_candidates.append(float(_recent_highs.iloc[-1]))
    _sl_candidates = [float(x) for x in _sl_candidates if x is not None and float(x) > entry_price]

    if _sl_candidates:
        # v6.17 CORRECTION: was max() - see matching note on the BUY side
        # above. Picking the FARTHEST above-entry candidate (e.g. today's
        # Unified Supply Zone top, ~590 pts away) instead of the nearest
        # real invalidation (sweep wick, ~20-30 pts away) is exactly what
        # produced the 22167.1 target / 588pt-risk case reported by the
        # user on 2026-09-22 - a distance no 5m-ATR-12.86 instrument moves
        # intraday. Nearest valid structural point = min() of the
        # above-entry candidates.
        stop_loss = round(min(_sl_candidates), 1)
        risk_points = round(stop_loss - entry_price, 1)
        if risk_points > 0:
            reward_points = round(risk_points * RR_RATIO, 1)
            target = round(entry_price - reward_points, 1)

            _opposing_wall = max(downside_walls) if downside_walls else None
            if _opposing_wall is None or target >= float(_opposing_wall):
                rr_valid = True
            else:
                rr_reject_reason = f"2R target {target} is beyond opposing wall {_opposing_wall}"
    else:
        rr_reject_reason = "No valid bearish structural invalidation level"

if final_signal in ("BUY", "SELL") and not rr_valid:
    # A structurally valid direction is still NEUTRAL if a clean 1:2 trade
    # cannot be achieved without moving the structural SL or target.
    final_signal = "NEUTRAL"

if final_signal == "NEUTRAL" and not rr_valid:
    # Do not expose stale trade levels after a RR rejection.
    if rr_reject_reason:
        print(f"RR FILTER -> NEUTRAL | {rr_reject_reason}")
    if primary_setup in ("BUY", "SELL"):
        stop_loss = None
        target = None
        risk_points = None
        reward_points = None

actual_rr = (
    round(abs(target - entry_price) / abs(entry_price - stop_loss), 2)
    if target is not None and stop_loss is not None and entry_price != stop_loss
    else None
)

# ============================================================
# v6.17 FIX: OPEN-TRADE STATE MACHINE (persists across cycles via
# state.json)
#
# PROBLEM THIS FIXES: every earlier cycle computed entry/SL/target from
# scratch and never looked at what an ALREADY-OPEN call from a previous
# cycle actually did against live price. So if a trade's SL or Target
# was hit three cycles later, the bot never said so - it just printed
# a fresh NEUTRAL/BUY/SELL, as if the earlier call had no continuing
# existence. This block is the fix: exactly one trade is tracked as
# "open" at a time, carried in state.json, and is resolved
# (TARGET_HIT / SL_HIT / REVERSED) before any new entry can replace it.
# ============================================================
trade_event = None             # "OPENED" / "TARGET_HIT" / "SL_HIT" / "REVERSED" / None
trade_closed_summary = None
current_open_trade = prev_open_trade
final_signal_is_new_entry = False

if prev_open_trade is not None:
    _dir = prev_open_trade["direction"]
    _entry = float(prev_open_trade["entry"])
    _sl = float(prev_open_trade["sl"])
    _tgt = float(prev_open_trade["target"])

    _hit_target = (nifty_ltp >= _tgt) if _dir == "BUY" else (nifty_ltp <= _tgt)
    _hit_sl = (nifty_ltp <= _sl) if _dir == "BUY" else (nifty_ltp >= _sl)
    if _hit_target and _hit_sl:
        # Both levels crossed within one 5m gap between cycles - we
        # cannot know intracandle which came first, so conservatively
        # record the worse outcome (SL) instead of assuming the win.
        _hit_target = False

    if _hit_target:
        _result_pts = round(abs(_tgt - _entry), 1)
        trade_event = "TARGET_HIT"
        trade_closed_summary = (
            f"TARGET HIT: {_dir} {_entry} -> {_tgt} "
            f"(+{_result_pts} pts, +{RR_RATIO:.1f}R)"
        )
        current_open_trade = None
    elif _hit_sl:
        _result_pts = round(abs(_entry - _sl), 1)
        trade_event = "SL_HIT"
        trade_closed_summary = (
            f"SL HIT: {_dir} {_entry} -> {_sl} "
            f"(-{_result_pts} pts, -1.0R)"
        )
        current_open_trade = None
    elif (
        final_signal in ("BUY", "SELL")
        and final_signal != _dir
        and (
            (final_signal == "BUY" and bull_groups >= 3)
            or (final_signal == "SELL" and bear_groups >= 3)
        )
    ):
        # v6.17 CORRECTION: reversal must NOT fire off primary_setup
        # alone. primary_setup can come from _early_5m_trigger(), which
        # is a SINGLE 5m candle read (body direction + break of prior
        # high/low + displacement >= 0.25*ATR) - it does not itself
        # check OI, Futures, or Zones. Closing a real open trade on that
        # one candle is exactly the "one parameter decided the signal"
        # problem. Reversal is now additionally gated on bull_groups/
        # bear_groups (>=3 of the 4 independent CORE_GROUPS - Futures/
        # Options/Zones/SMC - already computed earlier in the script,
        # same confluence bar the original v6.14 design used for entries)
        # actually agreeing with the new direction, not just the single
        # structural read.
        _running_pts = round((nifty_ltp - _entry) if _dir == "BUY" else (_entry - nifty_ltp), 1)
        trade_event = "REVERSED"
        trade_closed_summary = (
            f"REVERSED (closed - opposite signal + {bull_groups if final_signal == 'BUY' else bear_groups}/4 "
            f"groups confirmed): {_dir} {_entry} -> {round(nifty_ltp, 1)} "
            f"({'+' if _running_pts >= 0 else ''}{_running_pts} pts)"
        )
        current_open_trade = None
    elif final_signal in ("BUY", "SELL") and final_signal != _dir:
        # Opposite signal appeared but did NOT clear the 3-of-4 group
        # confluence bar - too weak (often just the single early-5m
        # candle) to close a real open trade. Trade stays open; this is
        # only noted, not acted on.
        trade_closed_summary = None
        print(
            f"REVERSAL SKIPPED -> opposite signal {final_signal} seen but only "
            f"{bull_groups if final_signal == 'BUY' else bear_groups}/4 groups agree "
            f"(need 3) - keeping existing {_dir} trade open"
        )
        current_open_trade = prev_open_trade
    else:
        # Still open. If this cycle produced the SAME direction again,
        # that is the ongoing trade continuing - NOT a new entry, and
        # it must not be reprinted as a fresh Entry/SL/Target block.
        current_open_trade = prev_open_trade

if current_open_trade is None and final_signal in ("BUY", "SELL"):
    current_open_trade = {
        "direction": final_signal,
        "entry": entry_price,
        "sl": stop_loss,
        "target": target,
        "opened_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    trade_event = trade_event or "OPENED"
    final_signal_is_new_entry = True

open_trade_status_text = None
if current_open_trade is not None:
    _d = current_open_trade["direction"]
    _e = float(current_open_trade["entry"])
    _s = float(current_open_trade["sl"]) if current_open_trade["sl"] is not None else None
    _t = current_open_trade["target"]
    _risk = abs(_e - _s) if _s is not None else None
    _running_pts = round((nifty_ltp - _e) if _d == "BUY" else (_e - nifty_ltp), 1)
    _running_r = round(_running_pts / _risk, 2) if _risk else None
    open_trade_status_text = (
        f"{_d} open | Entry {_e} | SL {_s} | Target {_t} | LTP {round(nifty_ltp, 1)} | "
        f"Running: {'+' if _running_pts >= 0 else ''}{_running_pts} pts"
        + (f" ({'+' if _running_r >= 0 else ''}{_running_r}R)" if _running_r is not None else "")
    )

# v6.17 FIX: SMC Trigger display used to be captured from primary_setup
# BEFORE the staleness/RR rejection below could still flip final_signal
# back to NEUTRAL - so the message could show "SMC Trigger: SELL" next
# to an overall NEUTRAL banner with no explanation, looking like a
# random contradiction. Now the reason is attached so it reads as one
# consistent decision instead of two disagreeing ones.
smc_trigger_rejection_reason = None
if smc_trigger in ("BUY", "SELL") and final_signal == "NEUTRAL":
    if entry_staleness_reject:
        smc_trigger_rejection_reason = "rejected this cycle - entry too stale, move already happened"
    elif rr_reject_reason:
        smc_trigger_rejection_reason = f"rejected this cycle - {rr_reject_reason}"
    elif atr_is_fallback:
        smc_trigger_rejection_reason = "rejected this cycle - ATR fallback active"
    else:
        smc_trigger_rejection_reason = "rejected this cycle - did not clear final filters"

# ============================================================
# EARLY WATCH (v6.14.5): NOT a confirmed signal, NEVER treated as
# one. Confirmation (sweep -> displacement -> BOS/CHOCH -> retest)
# can only ever be known after candle close - there is no way to
# know a move BEFORE it happens with certainty, and any tool that
# claims otherwise is lying. This block only flags that price is
# APPROACHING a zone with an early reaction candle (rejection wick)
# already forming - a heads-up to watch, not a trade call. It fires
# only when there is no confirmed signal this cycle, so it never
# competes with or dilutes a real BUY/SELL.
# ============================================================
def _early_watch_alert(df, zone_demand, zone_supply, atr):
    """
    Looks ONLY at the current (last closed) candle for an early
    reaction near a zone edge - price approaching within a wider
    tolerance than the confirmed-touch check, plus a rejection wick
    (long wick against the zone) that hasn't yet produced a full
    displacement/BOS/retest chain. Returns (direction, reason) or
    (None, None). This is explicitly a LEAN, not a confirmation.
    """
    if df is None or len(df) < 2 or atr is None or atr <= 0:
        return None, None

    last = df.iloc[-1]
    o, h, l, c = map(float, (last["open"], last["high"], last["low"], last["close"]))
    body = abs(c - o)
    lower_wick = min(o, c) - l
    upper_wick = h - max(o, c)
    watch_tolerance = 0.6 * atr  # wider than the 0.3*ATR confirmed-zone tolerance -
                                  # this is meant to catch price still APPROACHING,
                                  # not already fully inside/reacted.

    if zone_demand is not None:
        dist_to_demand = l - float(zone_demand["top"])
        near_demand = dist_to_demand <= watch_tolerance
        rejection_bull = lower_wick >= (1.3 * body if body > 0 else 0.3 * atr)
        not_strong_bear_close = c >= o - 0.1 * atr
        if near_demand and rejection_bull and not_strong_bear_close:
            return "BUY", (
                f"Approaching Demand zone ({zone_demand['bottom']}-{zone_demand['top']}) "
                f"with a rejection wick forming - watching for bullish confirmation "
                f"(sweep + displacement + BOS + retest still pending)"
            )

    if zone_supply is not None:
        dist_to_supply = float(zone_supply["bottom"]) - h
        near_supply = dist_to_supply <= watch_tolerance
        rejection_bear = upper_wick >= (1.3 * body if body > 0 else 0.3 * atr)
        not_strong_bull_close = c <= o + 0.1 * atr
        if near_supply and rejection_bear and not_strong_bull_close:
            return "SELL", (
                f"Approaching Supply zone ({zone_supply['bottom']}-{zone_supply['top']}) "
                f"with a rejection wick forming - watching for bearish confirmation "
                f"(sweep + displacement + BOS + retest still pending)"
            )

    return None, None


early_watch_direction, early_watch_reason = (None, None)
if final_signal == "NEUTRAL":
    early_watch_direction, early_watch_reason = _early_watch_alert(
        smc_df, unified_demand_zone, unified_supply_zone, atr_value
    )
    if early_watch_direction is not None:
        print(f"EARLY WATCH -> {early_watch_direction} (unconfirmed) | {early_watch_reason}")

print(
    f"Signal decision -> PRIMARY:{primary_setup} | Composite:{final_score} "
    f"| Bull/Bear confirmation groups:{bull_groups}/{bear_groups} "
    f"| VWAP/Open context:{price_above_vwap_and_open}/{price_below_vwap_and_open} "
    f"| 2R valid:{rr_valid} | Final Signal:{final_signal}"
)

# ============================================================
# Chart: last 60 candles (5m) with swing points + BOS/CHOCH labels
# ============================================================

# ============================================================
# SWING-BASED SUPPORT/RESISTANCE (price action, Time+Volume+Recency
# ranked) - adapted from support_resistance.py to match this bot's
# lowercase candle columns (time/open/high/low/close/volume) instead
# of the original ('Date'/'Open'/'High'/'Low'/'Close'/'Volume').
# This is INDEPENDENT of the existing OI-based support/resistance
# (max CE/PE OI strike) - it looks at actual swing high/low price
# clusters on the candle chart itself, confirmed by how many times
# price touched them, how much volume traded there, and how recent.
# ============================================================

def find_swing_sr_levels(df, window=5, min_touches=2, tolerance=0.002):
    """Cluster swing highs/lows into candidate support/resistance zones.
    Returns (support_levels, resistance_levels), each a list of
    (price, touch_count) tuples."""
    if df is None or df.empty or len(df) < (2 * window + 1):
        return [], []
    df = df.reset_index(drop=True)
    highs, lows = df["high"], df["low"]

    swing_highs, swing_lows = [], []
    for i in range(window, len(df) - window):
        if highs[i] == highs[i - window:i + window + 1].max():
            swing_highs.append(highs[i])
        if lows[i] == lows[i - window:i + window + 1].min():
            swing_lows.append(lows[i])

    def cluster_levels(prices):
        if not prices:
            return []
        prices = sorted(prices)
        clusters, current = [], [prices[0]]
        for p in prices[1:]:
            if abs(p - current[-1]) / current[-1] <= tolerance:
                current.append(p)
            else:
                clusters.append(current)
                current = [p]
        clusters.append(current)
        levels = [(float(np.mean(c)), len(c)) for c in clusters if len(c) >= min_touches]
        return sorted(levels, key=lambda x: -x[1])

    return cluster_levels(swing_lows), cluster_levels(swing_highs)


def calculate_swing_level_strength(df, level_price, tolerance=0.002, recency_halflife=50):
    """Time + Volume + Recency raw scores for one level (same 3-factor
    idea as the original script: how long price sat there, how much
    volume traded there, how recently it was touched)."""
    df = df.reset_index(drop=True)
    mask = (df["low"] <= level_price * (1 + tolerance)) & (df["high"] >= level_price * (1 - tolerance))
    touched = df[mask]

    time_score = len(touched)
    volume_score = touched["volume"].sum() if "volume" in df.columns else 0

    if len(touched) > 0:
        candles_ago = (len(df) - 1) - touched.index.values
        recency_score = np.exp(-candles_ago / recency_halflife).sum()
    else:
        recency_score = 0

    return {"time_score": time_score, "volume_score": volume_score, "recency_score": recency_score}


def rank_swing_sr_levels(df, levels, tolerance=0.002, recency_halflife=50, weights=(0.3, 0.4, 0.3)):
    """Score + rank levels from find_swing_sr_levels() by combined
    Time/Volume/Recency strength (0-1 normalized). Returns a list of
    dicts sorted strongest-first: [{'level':, 'touches':, 'strength':}, ...]"""
    if not levels:
        return []
    rows = []
    for level, touches in levels:
        s = calculate_swing_level_strength(df, level, tolerance, recency_halflife)
        rows.append({"level": level, "touches": touches, **s})

    max_t = max(r["time_score"] for r in rows) or 1
    min_t = min(r["time_score"] for r in rows)
    max_v = max(r["volume_score"] for r in rows) or 1
    min_v = min(r["volume_score"] for r in rows)
    max_r = max(r["recency_score"] for r in rows) or 1
    min_r = min(r["recency_score"] for r in rows)

    def norm(v, lo, hi):
        return 0.5 if hi - lo <= 0 else (v - lo) / (hi - lo)

    for r in rows:
        r["strength"] = (
            weights[0] * norm(r["time_score"], min_t, max_t)
            + weights[1] * norm(r["volume_score"], min_v, max_v)
            + weights[2] * norm(r["recency_score"], min_r, max_r)
        )
    return sorted(rows, key=lambda r: -r["strength"])


def build_chart(df, events, path="chart.png", resistance=None, support=None, maxpain=None, or_high=None, or_low=None,
                 order_blocks=None, fvg_list=None, liquidity_levels=None, latest_sweep=None, current_signal="NEUTRAL",
                 unified_demand_zone=None, unified_supply_zone=None,
                 swing_support_levels=None, swing_resistance_levels=None):
    """Current 5m chart with full SMC context. Historical zones are drawn only
    from their origin until mitigation/current candle, so refreshes evolve zones
    instead of leaving stale rectangles across the whole chart."""
    # CHART VIEW = latest available trading session only.
    # The analysis engine still uses the full historical dataset; only the
    # visual window is restricted so old 28-Aug/31-Aug candles do not keep
    # appearing after refresh.
    plot_df = df.copy()
    if not plot_df.empty:
        latest_session_date = plot_df["time"].dt.date.max()
        plot_df = plot_df[plot_df["time"].dt.date == latest_session_date].copy()
    plot_df = plot_df.reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(14, 8.3))
    n = len(plot_df)
    up_color, down_color = "#00b894", "#e74c3c"
    for i, row in plot_df.iterrows():
        color = up_color if row["close"] >= row["open"] else down_color
        ax.plot([i, i], [row["low"], row["high"]], color=color, linewidth=1, zorder=2)
        bottom = min(row["open"], row["close"]); height = abs(row["close"] - row["open"])
        if height <= 0: height = max((row["high"] - row["low"]) * 0.03, 0.01)
        ax.add_patch(patches.Rectangle((i - 0.3, bottom), 0.6, height, facecolor=color, edgecolor=color, zorder=3))

    # Day boundaries
    prev_date = None
    for i, t in enumerate(plot_df["time"]):
        d = t.date()
        if prev_date is not None and d != prev_date: ax.axvline(i - 0.5, color="gray", linestyle=":", linewidth=0.8, alpha=0.6)
        prev_date = d

    # Swings + BOS/CHOCH
    if "swing_high" in plot_df.columns:
        sh = plot_df[plot_df["swing_high"]]; ax.scatter(sh.index, sh["high"], marker="v", color="red", s=32, zorder=5)
        sl = plot_df[plot_df["swing_low"]]; ax.scatter(sl.index, sl["low"], marker="^", color="lime", s=32, zorder=5)
    time_to_idx = {t:i for i,t in enumerate(plot_df["time"])}
    for ev_time, ev_label, ev_price in events:
        # Only events belonging to the currently displayed session are
        # plotted as SMC events. Older events remain part of the analysis
        # engine but are not allowed to make the chart look stale.
        if ev_time in time_to_idx:
            idx=time_to_idx[ev_time]; col="lime" if "Bullish" in ev_label else "red"
            ax.annotate(ev_label, xy=(idx, ev_price), xytext=(0, 12), textcoords="offset points", fontsize=7, color=col, ha="center", rotation=90)

    session_start = plot_df["time"].iloc[0] if n else None

    def draw_zones(zones, bullish, label):
        if not zones or n == 0: return
        for z in zones:
            if z.get("top") is None or z.get("bottom") is None: continue
            ot=z.get("time")
            if ot is None: continue

            # Find the first interaction with this zone using the FULL
            # analysis dataset. If it was already mitigated before today's
            # session, don't draw that stale zone. If it is still active
            # from a prior session, start it at today's first candle.
            try:
                zone_df = df[df["time"] >= ot]
                mitigation_time = None
                for _, zr in zone_df.iloc[1:].iterrows():
                    if float(zr["low"]) <= float(z["top"]) and float(zr["high"]) >= float(z["bottom"]):
                        mitigation_time = zr["time"]
                        break
            except Exception:
                mitigation_time = None

            if mitigation_time is not None and session_start is not None and mitigation_time < session_start:
                continue

            if ot >= session_start:
                start_idx = time_to_idx.get(ot)
                if start_idx is None: continue
            else:
                # Historical zone still alive into the current session.
                start_idx = 0

            end_idx = n - 1
            for j in range(start_idx + 1, n):
                r=plot_df.iloc[j]
                if float(r["low"]) <= float(z["top"]) and float(r["high"]) >= float(z["bottom"]):
                    end_idx=j
                    break
            if end_idx < start_idx: end_idx=start_idx

            edge = "#00b894" if bullish else "#e74c3c"
            text_color = "#008f72" if bullish else "#b83227"
            ax.add_patch(patches.Rectangle((start_idx, z["bottom"]), max(end_idx-start_idx,1), z["top"]-z["bottom"],
                                            facecolor=edge, alpha=0.10, edgecolor=edge, linewidth=1.0, zorder=1))
            ax.text(start_idx, z["top"], label, fontsize=6, va="bottom", color=text_color)

    draw_zones([z for z in (order_blocks or []) if z.get("type")=="bullish"], True, "DEMAND/OB")
    draw_zones([z for z in (order_blocks or []) if z.get("type")=="bearish"], False, "SUPPLY/OB")
    # Explicit FVGs are separate imbalance zones.
    draw_zones([z for z in (fvg_list or []) if z.get("type")=="bullish"], True, "BULL FVG")
    draw_zones([z for z in (fvg_list or []) if z.get("type")=="bearish"], False, "BEAR FVG")

    # UNIFIED multi-source zone (NEW) - bolder band spanning the full
    # chart width, drawn on top of the individual per-source zones
    # above, labeled with how many independent sources agree on it.
    if n > 0:
        if unified_demand_zone is not None:
            ax.axhspan(unified_demand_zone["bottom"], unified_demand_zone["top"], color="#00b894", alpha=0.22, zorder=0.5)
            ax.text(n * 0.98, unified_demand_zone["top"],
                    f"DEMAND ZONE ({unified_demand_zone['strength']} sources)", fontsize=7.5, fontweight="bold",
                    color="#00794d", va="bottom", ha="right")
        if unified_supply_zone is not None:
            ax.axhspan(unified_supply_zone["bottom"], unified_supply_zone["top"], color="#e74c3c", alpha=0.22, zorder=0.5)
            ax.text(n * 0.98, unified_supply_zone["top"],
                    f"SUPPLY ZONE ({unified_supply_zone['strength']} sources)", fontsize=7.5, fontweight="bold",
                    color="#a71d0f", va="bottom", ha="right")

    # Liquidity map levels
    for lv in (liquidity_levels or []):
        price=lv.get("price")
        if price is not None:
            ax.axhline(float(price), color="purple", linestyle=":", linewidth=0.65, alpha=0.45)
            ax.text(max(0,n-1), float(price), " "+lv.get("label","Liquidity"), fontsize=6, color="purple", va="center")
    if latest_sweep and latest_sweep.get("time") in time_to_idx:
        idx=time_to_idx[latest_sweep["time"]]; price=float(latest_sweep.get("price", plot_df.iloc[idx]["close"]))
        ax.scatter([idx],[price], marker="*", s=90, color="orange", zorder=7)
        ax.annotate("LIQUIDITY SWEEP", (idx,price), xytext=(0,-18), textcoords="offset points", fontsize=7, color="orange", ha="center")

    if resistance is not None: ax.axhline(resistance, color="red", linestyle="--", linewidth=0.9, alpha=0.7, label="Resistance (CE OI)")
    if support is not None: ax.axhline(support, color="lime", linestyle="--", linewidth=0.9, alpha=0.7, label="Support (PE OI)")
    if maxpain is not None: ax.axhline(maxpain, color="orange", linestyle=":", linewidth=1.0, alpha=0.8, label="Max Pain")
    if or_high is not None: ax.axhline(or_high, color="cyan", linestyle="-.", linewidth=0.7, alpha=0.5)
    if or_low is not None: ax.axhline(or_low, color="cyan", linestyle="-.", linewidth=0.7, alpha=0.5)

    # Swing-based Support/Resistance (price action, Time+Volume+Recency
    # ranked) - separate from the OI-based lines above. Drawn as
    # dotted blue (support) / magenta (resistance) so they're visually
    # distinct from the red/lime OI walls.
    for lv in (swing_support_levels or []):
        price = lv["level"] if isinstance(lv, dict) else lv[0]
        touches = lv.get("touches") if isinstance(lv, dict) else (lv[1] if len(lv) > 1 else None)
        ax.axhline(price, color="#1f77ff", linestyle=":", linewidth=1.1, alpha=0.65)
        ax.text(max(0, n - 1), price, f" Swing S ({touches}x)" if touches else " Swing S",
                fontsize=6, color="#1f77ff", va="bottom", ha="left")
    for lv in (swing_resistance_levels or []):
        price = lv["level"] if isinstance(lv, dict) else lv[0]
        touches = lv.get("touches") if isinstance(lv, dict) else (lv[1] if len(lv) > 1 else None)
        ax.axhline(price, color="#c400c4", linestyle=":", linewidth=1.1, alpha=0.65)
        ax.text(max(0, n - 1), price, f" Swing R ({touches}x)" if touches else " Swing R",
                fontsize=6, color="#c400c4", va="top", ha="left")

    # ------------------------------------------------------------
    # LEGEND (NEW) - explicit proxy handles so Swing High/Low and the
    # Demand/Supply zone shading show up too, not just the plain
    # axhline() labels (which were being set but never rendered since
    # ax.legend() was never called before this fix).
    # ------------------------------------------------------------
    legend_handles = [
        Line2D([0], [0], marker="v", color="none", markerfacecolor="red", markeredgecolor="red", markersize=8, label="Swing High"),
        Line2D([0], [0], marker="^", color="none", markerfacecolor="lime", markeredgecolor="lime", markersize=8, label="Swing Low"),
        Line2D([0], [0], color="red", linestyle="--", linewidth=1.2, label="Resistance (CE OI)"),
        Line2D([0], [0], color="lime", linestyle="--", linewidth=1.2, label="Support (PE OI)"),
        Line2D([0], [0], color="orange", linestyle=":", linewidth=1.4, label="Max Pain"),
        Line2D([0], [0], color="cyan", linestyle="-.", linewidth=1.2, label="Opening Range"),
    ]
    if swing_support_levels:
        legend_handles.append(Line2D([0], [0], color="#1f77ff", linestyle=":", linewidth=1.2, label="Swing Support (price action)"))
    if swing_resistance_levels:
        legend_handles.append(Line2D([0], [0], color="#c400c4", linestyle=":", linewidth=1.2, label="Swing Resistance (price action)"))
    if unified_demand_zone is not None:
        legend_handles.append(Patch(facecolor="#00b894", alpha=0.35, label="Demand Zone"))
    if unified_supply_zone is not None:
        legend_handles.append(Patch(facecolor="#e74c3c", alpha=0.35, label="Supply Zone"))
    ax.legend(handles=legend_handles, loc="upper left", fontsize=7, framealpha=0.9)

    # ONLY current closed candle is highlighted for decision; no hindsight signal markers.
    if n:
        cur=n-1; r=plot_df.iloc[cur]
        ax.axvspan(cur-0.45, cur+0.45, alpha=0.12, color="gold")
        ax.annotate("CURRENT CLOSED 5m", (cur,float(r["high"])), xytext=(0,18), textcoords="offset points", fontsize=8, color="black", ha="center")
        ax.set_xticks(range(0,n,max(1,n//10)))
        ax.set_xticklabels([plot_df["time"].iloc[p].strftime("%d-%b %H:%M") for p in range(0,n,max(1,n//10))], rotation=45, ha="right")
        ax.set_xlim(-1,n)
    session_label = plot_df["time"].iloc[0].strftime("%d-%b") if n else "No Session"
    ax.set_title(f"NIFTY 50 - Live 5m SMC | {session_label} | Current Signal: {current_signal}")
    ax.grid(alpha=0.2, axis="y")

    # ------------------------------------------------------------
    # KEY TAKEAWAY + PLAN boxes (NEW) - auto-generated from the SAME
    # live data the chart just drew (latest sweep, latest BOS/CHOCH
    # event, unified Demand/Supply zones). Not hardcoded text - this
    # updates every cycle with whatever actually happened this session.
    # ------------------------------------------------------------
    last_event_label = events[-1][1] if events else None
    trend_bias = (
        "bullish" if last_event_label and "Bullish" in last_event_label
        else "bearish" if last_event_label and "Bearish" in last_event_label
        else "mixed/unclear"
    )

    takeaway_lines = []
    if latest_sweep:
        sweep_price = latest_sweep.get("price")
        takeaway_lines.append(
            f"Price swept liquidity at {round(float(sweep_price)) if sweep_price is not None else 'N/A'} "
            f"and showed a {trend_bias} reaction."
        )
    if last_event_label:
        takeaway_lines.append(f"Trend structure turned {trend_bias} after {last_event_label}.")
    if unified_demand_zone is not None and unified_supply_zone is not None:
        near_demand = plot_df["close"].iloc[-1] <= unified_demand_zone["top"] if n else False
        near_supply = plot_df["close"].iloc[-1] >= unified_supply_zone["bottom"] if n else False
        if near_demand:
            takeaway_lines.append("Price is currently near the Demand Zone.")
        elif near_supply:
            takeaway_lines.append("Price is currently near the Supply Zone.")
        else:
            takeaway_lines.append("Price is currently moving between Demand and Supply zones.")
    if not takeaway_lines:
        takeaway_lines = ["No confirmed liquidity sweep / structure shift this session yet."]

    plan_lines = []
    if unified_demand_zone is not None:
        target_up = round(unified_supply_zone["bottom"]) if unified_supply_zone is not None else None
        plan_lines.append(
            "Bullish Scenario: Buy on demand zone / FVG retest"
            + (f" for move to {target_up}+" if target_up is not None else "")
        )
    if unified_supply_zone is not None:
        target_dn = round(unified_demand_zone["top"]) if unified_demand_zone is not None else None
        plan_lines.append(
            "Bearish Scenario: Rejection from supply zone"
            + (f" for move back to {target_dn}" if target_dn is not None else "")
        )
    if not plan_lines:
        plan_lines = ["No active zone-based plan this session."]

    fig.tight_layout(rect=[0, 0.14, 1, 1])  # reserve bottom strip for the two boxes

    takeaway_text = "KEY TAKEAWAY\n" + "\n".join(f"\u2022 {t}" for t in takeaway_lines)
    plan_text = "PLAN\n" + "\n".join(plan_lines)

    fig.text(0.02, 0.02, takeaway_text, fontsize=8, va="bottom", ha="left",
              color="black", family="sans-serif",
              bbox=dict(boxstyle="round,pad=0.6", facecolor="white", edgecolor="#333333", linewidth=1))
    fig.text(0.55, 0.02, plan_text, fontsize=8, va="bottom", ha="left",
              color="black", family="sans-serif",
              bbox=dict(boxstyle="round,pad=0.6", facecolor="white", edgecolor="#333333", linewidth=1))

    fig.savefig(path, dpi=130); plt.close(fig); return path


# ============================================================
# Swing-based Support/Resistance (price action) - computed from the
# full smc_df (15 days of 5m candles) so there's enough history for
# genuine swing clusters, then ranked by Time+Volume+Recency and only
# the top 2 strongest per side are kept for the chart (avoids clutter).
# ============================================================
try:
    raw_swing_support, raw_swing_resistance = find_swing_sr_levels(smc_df, window=5, min_touches=2, tolerance=0.002)
    swing_support_ranked = rank_swing_sr_levels(smc_df, raw_swing_support)[:2]
    swing_resistance_ranked = rank_swing_sr_levels(smc_df, raw_swing_resistance)[:2]
except Exception as e:
    print(f"Swing S/R calculation failed: {e}")
    swing_support_ranked, swing_resistance_ranked = [], []

chart_path = None
try:
    chart_path = build_chart(
        smc_df, smc_events,
        resistance=resistance_strike, support=support_strike, maxpain=maxpain_strike,
        or_high=or_high, or_low=or_low, order_blocks=order_blocks, fvg_list=fvg_list,
        liquidity_levels=liquidity_levels, latest_sweep=latest_liquidity_sweep, current_signal=final_signal,
        unified_demand_zone=unified_demand_zone, unified_supply_zone=unified_supply_zone,
        swing_support_levels=swing_support_ranked, swing_resistance_levels=swing_resistance_ranked,
    )
except Exception as e:
    print("Chart build error (non-fatal):", e)


# ============================================================
# THE MISSING PIECE: build and SEND the Telegram message for the
# actual live signal. Every previous version only ever called
# telegram_message() for the one-time first-run baseline text -
# this is the call that was never wired up for real BUY/SELL/
# NEUTRAL cycles, which is why no alerts were arriving.
# ============================================================

signal_emoji = {
    "STRONG BUY": "\U0001F7E2\U0001F7E2", "BUY": "\U0001F7E2",
    "STRONG SELL": "\U0001F534\U0001F534", "SELL": "\U0001F534",
    "NEUTRAL": "\u26AA",
}.get(final_signal, "\u26AA")

def fmt(v, suffix="", decimals=1):
    return f"{round(v, decimals)}{suffix}" if v is not None else "N/A"

lines = [
    f"{signal_emoji} UMI BOT Signal: {final_signal}",
    f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
    "",

    "--- LEVEL 1: Market Regime ---",
    f"NIFTY: {nifty_ltp} ({arrow(nifty_change)} {nifty_change:+.2f})",
    f"Midcap Nifty: {midcap_price} ({arrow(midcap_change)} {midcap_change:+.2f}) | Bank Nifty: {banknifty_price} ({arrow(banknifty_change)} {banknifty_change:+.2f})",
    f"VWAP: {fmt(vwap_value)} | Session Open: {fmt(session_open)} | Bias: {vwap_bias or 'N/A'}",
    f"Opening Range: {fmt(or_low)}-{fmt(or_high)} | ORB Score: {orb_score}",
    f"ATR(14,5m): {atr_value:.2f}",
    f"India VIX: {india_vix if india_vix is not None else 'N/A'} | Vol Regime: {vol_regime} | Strike Range: +/-{STRIKE_RANGE}",
    f"VIX Band: {vix_band} ({vix_premium_note}) | Percentile: {vix_percentile if vix_percentile is not None else 'N/A'} | Trend: {vix_trend}",
    f"VIX Expected Move: +/-{vix_move['move_points'] if vix_move else 'N/A'} pts (S:{vix_move['support'] if vix_move else 'N/A'} R:{vix_move['resistance'] if vix_move else 'N/A'})",
    f"VIX Signal: {vix_signal_direction} (confidence {vix_signal_confidence:.2f}) | Score: {vix_signal_score}",
    "",

    "--- LEVEL 2: Futures Institutional Positioning ---",
    f"{NIFTY_FUT_SYMBOL}: {fut_ltp} ({arrow(fut_change)} {fut_change:+.2f})",
    f"Futures OI: {arrow(fut_oi_change)}{fut_oi_change:+.0f} (total {fut_oi:.0f})",
    f"Futures Price+OI: {futures_price_action}",
    f"FII Index Futures (as of {fii_fut_as_of or 'N/A'}): Long {fmt(fii_fut_long,decimals=0)} / Short {fmt(fii_fut_short,decimals=0)} | Ratio {fmt(fii_fut_ratio,decimals=3)}",
    "",

    "--- LEVEL 3: Option Chain Positioning ---",
    f"OI: CE {arrow(ce_oi_change)}{ce_oi_change:+.0f} | PE {arrow(pe_oi_change)}{pe_oi_change:+.0f}",
    f"Volume: CE {arrow(ce_vol_change)}{ce_vol_change:+.0f} | PE {arrow(pe_vol_change)}{pe_vol_change:+.0f}",
    f"PCR (OI): {fmt(pcr, decimals=2)} | ChgOI: {fmt(pcr_change_oi, decimals=2)} | Vol: {fmt(pcr_volume, decimals=2)} | OTM: {fmt(pcr_otm, decimals=2)}",
    f"PCR Read: {pcr_interpretation['label']}"
    + (f" (percentile {pcr_interpretation['percentile']})" if pcr_interpretation['percentile'] is not None else ""),
    f"PCR Trend (30m): {pcr_trend}",
    f"Near-ATM (+/-100): Call Writing {call_writing_ct} | Call Unwinding {call_unwinding_ct} | "
    f"Put Writing {put_writing_ct} | Put Unwinding {put_unwinding_ct}",
    "",

    "--- LEVEL 4: Institutional Zones ---",
    f"Max Pain: {fmt(maxpain_strike, decimals=0)}",
    f"Resistance (OI-based, big pile): {fmt(resistance_strike, decimals=0)} | Support (OI-based, big pile): {fmt(support_strike, decimals=0)}",
    f"Resistance (ChgOI-based, fresh writing today): {fmt(resistance_chgoi_strike, decimals=0)} | Support (ChgOI-based, fresh writing today): {fmt(support_chgoi_strike, decimals=0)}",
    f"Resistance Strength: {_strength_tag(resistance_strengthening, resistance_multi_day, prev_day_resistance_strike)} | Support Strength: {_strength_tag(support_strengthening, support_multi_day, prev_day_support_strike)}",
    f"Swing Resistance (price action): {', '.join(fmt(r['level'], decimals=0) for r in swing_resistance_ranked) if swing_resistance_ranked else 'N/A'} | "
    f"Swing Support (price action): {', '.join(fmt(s['level'], decimals=0) for s in swing_support_ranked) if swing_support_ranked else 'N/A'}",
    f"OI Concentration (top 3 strikes): CE {fmt(ce_concentration_pct,'%')} | PE {fmt(pe_concentration_pct,'%')}",
    f"Fresh Call Writing: {fmt(fresh_call_writing_strike, decimals=0)} | Fresh Put Writing: {fmt(fresh_put_writing_strike, decimals=0)}",
    "",
    f"UNIFIED DEMAND ZONE: {round(unified_demand_zone['bottom'],1)}-{round(unified_demand_zone['top'],1)} "
    f"[Sources: {', '.join(unified_demand_zone['sources'])}]"
    f" | Multi-day confirmed: {'YES' if unified_demand_zone.get('multi_day_confirmed') else 'No'}" if unified_demand_zone else "UNIFIED DEMAND ZONE: N/A",
    f"UNIFIED SUPPLY ZONE: {round(unified_supply_zone['bottom'],1)}-{round(unified_supply_zone['top'],1)} "
    f"[Sources: {', '.join(unified_supply_zone['sources'])}]"
    f" | Multi-day confirmed: {'YES' if unified_supply_zone.get('multi_day_confirmed') else 'No'}" if unified_supply_zone else "UNIFIED SUPPLY ZONE: N/A",
    "(standalone, option-chain only - NOT mixed with 1H/30M confirmation above)",
    f"OI DEMAND ZONE: {round(oi_demand_zone['bottom'],1)}-{round(oi_demand_zone['top'],1)} [{oi_demand_zone['sources'][0]}]" if oi_demand_zone else "OI DEMAND ZONE: N/A",
    f"OI SUPPLY ZONE: {round(oi_supply_zone['bottom'],1)}-{round(oi_supply_zone['top'],1)} [{oi_supply_zone['sources'][0]}]" if oi_supply_zone else "OI SUPPLY ZONE: N/A",
    f"ChgOI DEMAND ZONE: {round(chgoi_demand_zone['bottom'],1)}-{round(chgoi_demand_zone['top'],1)} [{chgoi_demand_zone['sources'][0]}]" if chgoi_demand_zone else "ChgOI DEMAND ZONE: N/A",
    f"ChgOI SUPPLY ZONE: {round(chgoi_supply_zone['bottom'],1)}-{round(chgoi_supply_zone['top'],1)} [{chgoi_supply_zone['sources'][0]}]" if chgoi_supply_zone else "ChgOI SUPPLY ZONE: N/A",
    f"(single-source only) Demand Zone (OB): {round(nearest_demand['bottom'],1)}-{round(nearest_demand['top'],1)}" if nearest_demand else "(single-source only) Demand Zone (OB): N/A",
    f"(single-source only) Supply Zone (OB): {round(nearest_supply['bottom'],1)}-{round(nearest_supply['top'],1)}" if nearest_supply else "(single-source only) Supply Zone (OB): N/A",
    f"Bullish FVG (unfilled): {round(nearest_fvg_demand['bottom'],1)}-{round(nearest_fvg_demand['top'],1)}" if nearest_fvg_demand else "Bullish FVG (unfilled): N/A",
    f"Bearish FVG (unfilled): {round(nearest_fvg_supply['bottom'],1)}-{round(nearest_fvg_supply['top'],1)}" if nearest_fvg_supply else "Bearish FVG (unfilled): N/A",
    f"Active FVGs: {len(fvg_list)}",
    f"Structure (last 4 swings): {' -> '.join(p['label'] for p in structure_points[-4:]) if structure_points else 'N/A'}",
    f"Location (context only, NOT used for Buy/Sell): {'Near Demand Zone' if near_demand_zone else ('Near Supply Zone' if near_supply_zone else 'Not near either zone')}",
    f"S/D Cross-Check - Demand (confirmation only): {sd_demand_cross_check_text}",
    f"S/D Cross-Check - Supply (confirmation only): {sd_supply_cross_check_text}",
    "",

    "--- LEVEL 5: Price + Flow Confirmation (Futures-based) ---",
    f"{futures_price_action}",
    "",

    "--- LEVEL 6: SMC ---",
    f"PDH/PDL: {fmt(pdh,decimals=0)} / {fmt(pdl,decimals=0)} | PWH/PWL: {fmt(pwh,decimals=0)} / {fmt(pwl,decimals=0)}",
    f"Equal Highs (BSL): {fmt(bsl_level,decimals=0)} | Equal Lows (SSL): {fmt(ssl_level,decimals=0)}",
    f"Recent Swing High/Low: {fmt(recent_swing_high,decimals=0)} / {fmt(recent_swing_low,decimals=0)}",
    f"Liquidity Sweeps this cycle: {len(swept_levels)} raw, {len(confirmed_sweeps)} structurally confirmed "
    f"(Rejection+Displacement+BOS/CHOCH)"
    + (f" | Latest: {latest_liquidity_sweep['label']} ({latest_liquidity_sweep['type']})" if latest_liquidity_sweep else ""),
    f"Liquidity Map Final Direction: {'Bullish' if liquidity_score > 0 else ('Bearish' if liquidity_score < 0 else 'Unconfirmed/None')} "
    f"(price-structure confirmed; Volume/OI are conviction only)",
    f"SMC Trigger (CURRENT CLOSED CANDLE): {smc_trigger}"
    + (f" [{smc_trigger_rejection_reason}]" if smc_trigger_rejection_reason else ""),
    "",

    "--- Global Cues ---",
]
for label, pct in global_cues.items():
    lines.append(f"  {label}: {pct:+.2f}%" if pct is not None else f"  {label}: N/A")

lines += [
    "",
    f"FII (prev day, cash): {fii_net}",
    f"DII (prev day, cash): {dii_net}",
]

lines += [
    "",
    "--- TRADE STATUS ---",
]
if trade_closed_summary:
    lines.append(f"\u26aa {trade_closed_summary}")
if current_open_trade is not None:
    if final_signal_is_new_entry:
        lines += [
            f"NEW ENTRY: {current_open_trade['direction']}",
            f"Entry: {current_open_trade['entry']}",
            f"SL: {current_open_trade['sl']} | Risk: {risk_points} pts",
            f"Target: {current_open_trade['target']} | Reward: {reward_points} pts",
            f"Risk:Reward = 1:{actual_rr:.2f}" if actual_rr is not None else "Risk:Reward = N/A",
            "Order execution: MANUAL ONLY (no auto place/exit)",
        ]
    else:
        lines.append(f"OPEN TRADE (continuing, not a new entry): {open_trade_status_text}")
elif not trade_closed_summary:
    lines.append("No open trade.")

message_text = "\n".join(lines)

if chart_path:
    telegram_send_photo(chart_path, caption=message_text[:1024])
    if len(message_text) > 1024:
        telegram_message(message_text)
else:
    telegram_message(message_text)

# ============================================================
# EARLY WATCH message - sent ONLY when there's no confirmed signal
# this cycle. Deliberately a separate message with its own header so
# it can never be mistaken for a confirmed BUY/SELL. Deduped against
# the previous cycle's alert (same direction + same zone) so it
# doesn't repeat every cycle while price just sits near the zone -
# it only re-fires if the direction changes or it clears and comes
# back.
# ============================================================
current_early_watch_key = f"{early_watch_direction}" if early_watch_direction else None
if early_watch_direction is not None and current_early_watch_key != prev_early_watch:
    watch_lines = [
        "\u26a0\ufe0f EARLY WATCH (UNCONFIRMED - NOT A SIGNAL)",
        f"Lean: {early_watch_direction}",
        early_watch_reason,
        f"LTP: {nifty_ltp}",
        "",
        "This is NOT a confirmed BOS/CHOCH + retest setup - it is only an early "
        "reaction candle near a zone. It can fail. No entry/SL/target until the "
        "full structural chain confirms in a later cycle.",
    ]
    telegram_message("\n".join(watch_lines))
    print(f"EARLY WATCH message sent -> {early_watch_direction}")


# ============================================================
# Save state for the next cycle - extended with Level 2 (futures),
# Level 2 (FII futures ratio), and Level 3 (per-strike) data so the
# next cycle can diff against all of it.
# ============================================================

save_state({
    "ce_oi": ce_oi_total, "pe_oi": pe_oi_total,
    "ce_vol": ce_vol_total, "pe_vol": pe_vol_total,
    "nifty": nifty_ltp, "midcap": midcap_price, "banknifty": banknifty_price,
    "fut_ltp": fut_ltp, "fut_oi": fut_oi,
    "fii_fut_ratio": fii_fut_ratio if fii_fut_ratio is not None else prev_fii_fut_ratio,
    "strike_oi": current_strike_snapshot,
    "sr_history": sr_history,
    "pcr_history": pcr_history,
    "vix_history": vix_history,
    "last_early_watch": current_early_watch_key,
    "market_behaviour": market_behaviour,
    "last_final_signal": final_signal,
    "zone_track_date": today_ist_date,
    "zone_track_demand": _raw_demand_zone_snapshot,
    "zone_track_supply": _raw_supply_zone_snapshot,
    "prev_day_zone_date": prev_day_zone_date,
    "prev_day_demand_zone": prev_day_demand_zone,
    "prev_day_supply_zone": prev_day_supply_zone,
    "sr_track_date": today_ist_date,
    "sr_track_resistance": resistance_strike,
    "sr_track_support": support_strike,
    "prev_day_sr_date": prev_day_sr_date,
    "prev_day_resistance_strike": prev_day_resistance_strike,
    "prev_day_support_strike": prev_day_support_strike,
    "vix_cache_date": _vix_cache_date,
    "vix_cache_morning_done": _vix_cache_morning_done,
    "vix_cache_midday_done": _vix_cache_midday_done,
    "vix_cache_value": _vix_cache_value,
    "open_trade": current_open_trade,
})

print(f"Cycle complete. Signal: {final_signal} | Composite Score: {final_score} "
      f"| Bull/Bear Groups: {bull_groups}/{bear_groups}")


