# =========================
# backend/infrastructure/market/yfinance_adapter.py
# =========================
from __future__ import annotations
import io
import logging
import os
import time
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

import pandas as pd
import pytz
import yfinance as yf
from yfinance.exceptions import YFRateLimitError

from domain.ports.market_data import MarketDataRepo, MarketStatus
from domain.entities.market_data import PriceData, PriceSource, SimulationData
from infrastructure.market.market_data_storage import MarketDataStorage
from infrastructure.market.data_validator import DataValidator


class YFinanceAdapter(MarketDataRepo):
    """yfinance implementation of market data repository with comprehensive storage."""

    _print_once_patched = False

    def __init__(self):
        self.tz_eastern = pytz.timezone("US/Eastern")
        self.tz_utc = timezone.utc
        self.storage = MarketDataStorage()
        self.cache_ttl = 30  # 30 seconds cache TTL (reduced from 5 to allow more frequent updates)
        self.last_error_kind: Optional[str] = None
        self.last_error: Optional[Exception] = None
        self._logger = logging.getLogger(__name__)
        self._patch_print_once()

    def _ticker(self, symbol: str) -> yf.Ticker:
        """Return a yfinance Ticker. Let yfinance manage its own session (curl_cffi)."""
        return yf.Ticker(symbol)

    def _fetch_via_chart_api(self, ticker: str) -> Optional[PriceData]:
        """
        Direct HTTP call to Yahoo Finance chart API — bypasses yfinance entirely.
        Uses the v8/finance/chart endpoint which is less aggressively blocked on
        cloud IPs than the quote/quoteSummary endpoints.
        Returns PriceData on success, None on failure.
        """
        current_time = datetime.now(self.tz_utc)
        for host in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
            url = f"https://{host}/v8/finance/chart/{ticker}"
            params = {"interval": "1d", "range": "5d", "includePrePost": "false"}
            try:
                resp = __import__('requests').get(url, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                result = data.get("chart", {}).get("result")
                if not result:
                    continue
                quotes = result[0]["indicators"]["quote"][0]
                closes = quotes.get("close", [])
                price = next((c for c in reversed(closes) if c is not None), None)
                if not price or price <= 0:
                    continue
                timestamps = result[0].get("timestamp", [])
                last_ts = current_time
                if timestamps:
                    last_ts = datetime.fromtimestamp(timestamps[-1], tz=self.tz_utc)
                opens = quotes.get("open", [])
                highs = quotes.get("high", [])
                lows = quotes.get("low", [])
                volumes = quotes.get("volume", [])
                last_open = next((v for v in reversed(opens) if v is not None), None)
                last_high = next((v for v in reversed(highs) if v is not None), None)
                last_low = next((v for v in reversed(lows) if v is not None), None)
                last_vol = next((v for v in reversed(volumes) if v is not None), None)
                price_data = PriceData(
                    ticker=ticker,
                    price=price,
                    source=PriceSource.LAST_TRADE,
                    timestamp=current_time,
                    bid=price * 0.999,
                    ask=price * 1.001,
                    volume=int(last_vol) if last_vol else None,
                    last_trade_price=price,
                    last_trade_time=last_ts,
                    is_market_hours=False,
                    is_fresh=False,
                    is_inline=False,
                    open=last_open,
                    high=last_high,
                    low=last_low,
                    close=price,
                )
                self.storage.store_price_data(ticker, price_data)
                print(f"✅ Chart API fallback succeeded for {ticker}: ${price:.2f} via {host}")
                return price_data
            except Exception as e:
                print(f"⚠️ Chart API fallback failed for {ticker} via {host}: {e}")
        return None

    def _fetch_via_stooq(self, ticker: str) -> Optional[PriceData]:
        """
        Fetch last close price from Stooq (stooq.com) — a free financial data site
        that does NOT block cloud/datacenter IPs, unlike Yahoo Finance.
        Returns PriceData with is_fresh=False (previous close), or None on failure.
        Stooq uses a different ticker format: US stocks append '.US' (e.g. ZIM.US).
        """
        import csv
        import io as _io

        current_time = datetime.now(self.tz_utc)
        # Stooq ticker format: append .US for US-listed equities
        stooq_symbol = ticker if "." in ticker else f"{ticker}.US"
        url = f"https://stooq.com/q/d/l/?s={stooq_symbol}&i=d"
        try:
            resp = __import__('requests').get(url, timeout=10)
            resp.raise_for_status()
            text = resp.text.strip()
            if not text or "No data" in text:
                print(f"⚠️ Stooq returned no data for {stooq_symbol}")
                return None
            reader = csv.DictReader(_io.StringIO(text))
            rows = list(reader)
            if not rows:
                return None
            last = rows[-1]
            price = float(last.get("Close") or last.get("close") or 0)
            if price <= 0:
                return None
            open_ = float(last.get("Open") or last.get("open") or price)
            high = float(last.get("High") or last.get("high") or price)
            low = float(last.get("Low") or last.get("low") or price)
            vol = last.get("Volume") or last.get("volume")
            volume = int(float(vol)) if vol else None
            date_str = last.get("Date") or last.get("date") or ""
            try:
                last_ts = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=self.tz_utc)
            except Exception:
                last_ts = current_time
            price_data = PriceData(
                ticker=ticker,
                price=price,
                source=PriceSource.LAST_TRADE,
                timestamp=current_time,
                bid=price * 0.999,
                ask=price * 1.001,
                volume=volume,
                last_trade_price=price,
                last_trade_time=last_ts,
                is_market_hours=False,
                is_fresh=False,
                is_inline=False,
                open=open_,
                high=high,
                low=low,
                close=price,
            )
            self.storage.store_price_data(ticker, price_data)
            print(f"✅ Stooq fallback succeeded for {ticker}: ${price:.2f} (last close {date_str})")
            return price_data
        except Exception as e:
            print(f"⚠️ Stooq fallback failed for {ticker}: {e}")
            return None

    def _deterministic_guard(self, ticker: str) -> bool:
        if os.getenv("TICK_DETERMINISTIC", "").lower() in {"1", "true", "yes", "on"}:
            self._logger.warning(
                "Deterministic mode enabled; skipping real market data fetch for %s",
                ticker,
            )
            return True
        return False

    def _patch_print_once(self) -> None:
        if YFinanceAdapter._print_once_patched:
            return
        if os.getenv("YFINANCE_SILENCE_PRINT_ONCE", "true").lower() != "true":
            return
        try:
            from yfinance import utils as yf_utils

            def _quiet_print_once(message: str) -> None:
                if os.getenv("YFINANCE_LOG_OUTPUT", "false").lower() == "true":
                    self._logger.debug("Suppressed yfinance print_once: %s", message)

            yf_utils.print_once = _quiet_print_once
            YFinanceAdapter._print_once_patched = True
        except Exception:
            self._logger.debug("Unable to patch yfinance print_once", exc_info=True)

    @contextmanager
    def _suppress_yfinance_output(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            yield
        if os.getenv("YFINANCE_LOG_OUTPUT", "false").lower() == "true":
            output = (stdout.getvalue() + stderr.getvalue()).strip()
            if output:
                self._logger.debug("Suppressed yfinance output: %s", output)

    def clear_cache(self, ticker: str = None):
        """Clear cached price data for a ticker or all tickers."""
        self.storage.clear_price_cache(ticker)

    def _get_cached_price(self, ticker: str, allow_stale: bool = False) -> Optional[PriceData]:
        """Return cached price data if present (optionally allow stale)."""
        cached = self.storage.price_cache.get(ticker)
        if not cached:
            return None
        age_seconds = (datetime.now(self.tz_utc) - cached.timestamp).total_seconds()
        if age_seconds <= self.cache_ttl:
            return cached
        if allow_stale:
            return self._mark_price_stale(cached)
        return None

    def _mark_price_stale(self, price_data: PriceData) -> PriceData:
        """Return a copy of price data marked as stale."""
        return PriceData(
            ticker=price_data.ticker,
            price=price_data.price,
            source=price_data.source,
            timestamp=price_data.timestamp,
            bid=price_data.bid,
            ask=price_data.ask,
            volume=price_data.volume,
            last_trade_price=price_data.last_trade_price,
            last_trade_time=price_data.last_trade_time,
            is_market_hours=price_data.is_market_hours,
            is_fresh=False,
            is_inline=price_data.is_inline,
            open=price_data.open,
            high=price_data.high,
            low=price_data.low,
            close=price_data.close,
        )

    def get_price(self, ticker: str, force_refresh: bool = False) -> Optional[PriceData]:
        """Get current price data for a ticker with cache + retry backoff."""
        if self._deterministic_guard(ticker):
            return None
        self.last_error_kind = None
        self.last_error = None
        cached = self._get_cached_price(ticker, allow_stale=False)
        if cached and not force_refresh:
            print(f"✅ Using cached price for {ticker} (age within TTL)")
            return cached
        if cached and force_refresh:
            print(f"⚠️ Using cached price for {ticker} to avoid frequent refresh")
            return cached

        stale_cached = self._get_cached_price(ticker, allow_stale=True)
        retry_delays = [1, 2, 4]
        last_error: Optional[Exception] = None

        for attempt, delay in enumerate([0] + retry_delays):
            if delay:
                time.sleep(delay)
            try:
                result = self._fetch_price_uncached(ticker, force_refresh=force_refresh)
                if result is None:
                    self.last_error_kind = "not_found"
                    self._logger.info("No market data found for %s", ticker)
                    return None
                return result
            except YFRateLimitError as e:
                last_error = e
                self.last_error_kind = "provider_unavailable"
                print(f"⚠️ Rate limited fetching {ticker} (attempt {attempt + 1})")
                if stale_cached:
                    print(f"⚠️ Returning cached price for {ticker} due to rate limit")
                    return stale_cached
                if attempt == len(retry_delays):
                    break
            except Exception as e:
                last_error = e
                self._set_error_kind(e)
                break

        if stale_cached:
            print(f"⚠️ Returning cached price for {ticker} after error: {last_error}")
            return stale_cached
        if last_error:
            if self.last_error_kind == "not_found":
                self._logger.info("No market data found for %s", ticker)
            elif self.last_error_kind == "provider_unavailable":
                self._logger.warning("Market data provider unavailable for %s", ticker)
            else:
                self._logger.exception("Unexpected market data error for %s", ticker)
        return None

    def _set_error_kind(self, error: Exception) -> None:
        message = str(error)
        normalized = message.lower()
        if isinstance(error, ValueError) and "Invalid ticker" in message:
            self.last_error_kind = "not_found"
            return
        if isinstance(error, AttributeError) and "update" in message:
            self.last_error_kind = "not_found"
            return
        if (
            "no data found" in normalized
            or "possibly delisted" in normalized
            or ("quotesummary" in normalized and "404" in normalized)
            or "404 client error" in normalized
        ):
            self.last_error_kind = "not_found"
            return
        if isinstance(error, YFRateLimitError):
            self.last_error_kind = "provider_unavailable"
            return
        self.last_error_kind = "provider_unavailable"

    def _fetch_price_uncached(self, ticker: str, force_refresh: bool = False) -> Optional[PriceData]:
        """Get current price data for a ticker (uncached).

        Args:
            ticker: Stock ticker symbol
            force_refresh: If True, bypass cache and fetch fresh data
        """
        try:
            # NEVER use cache for get_price - always fetch fresh data
            # The cache might contain weeks-old data from previous runs
            print(f"🔍 Fetching fresh market data for {ticker} (cache bypassed)")

            # Fetch fresh data using multiple methods for better accuracy
            # Create a NEW Ticker instance each time to avoid yfinance caching
            stock = self._ticker(ticker)
            # Force refresh by accessing info with a fresh request
            current_time = datetime.now(self.tz_utc)

            # ALWAYS try fast_info first (most current data)
            try:
                # Access fast_info - this should be fresh
                with self._suppress_yfinance_output():
                    fast_info = stock.fast_info
                # fast_info has the most current data
                current_price = (
                    fast_info.get("lastPrice")
                    or fast_info.get("regularMarketPrice")
                    or fast_info.get("previousClose")
                )
                bid = fast_info.get("bid")
                ask = fast_info.get("ask")

                if current_price and current_price > 0:
                    # Use fast_info data (most current)
                    mid_quote = (
                        (bid + ask) / 2 if (bid and ask and bid > 0 and ask > 0) else current_price
                    )
                    price = current_price
                    source = PriceSource.LAST_TRADE
                    is_fresh = True
                    is_inline = True
                    last_trade_price = current_price
                    last_trade_time = current_time  # Use current time for fast_info

                    # Get volume from fast_info if available
                    volume = fast_info.get("regularMarketVolume") or fast_info.get("volume")

                    # Fetch today's OHLC data - prefer intraday from info object (most current during market hours)
                    today_ohlc = None
                    try:
                        # Get fresh info object - this has the most current intraday OHLC values
                        # Create a NEW ticker instance to ensure fresh data (yfinance may cache)
                        fresh_stock = self._ticker(ticker)
                        with self._suppress_yfinance_output():
                            info = fresh_stock.info

                        # Debug: log what we're getting from info
                        print(
                            f"🔍 Debug {ticker} info values: regularMarketOpen={info.get('regularMarketOpen')}, regularMarketDayHigh={info.get('regularMarketDayHigh')}, regularMarketDayLow={info.get('regularMarketDayLow')}"
                        )

                        # Use intraday values from info (most accurate during market hours)
                        day_open = info.get("regularMarketOpen") or info.get("open")
                        day_high = info.get("regularMarketDayHigh") or info.get("dayHigh")
                        day_low = info.get("regularMarketDayLow") or info.get("dayLow")
                        day_close = (
                            current_price  # Use current price as today's close (most recent)
                        )

                        # If we have at least open, use it (high/low might not be available early in the day)
                        if day_open:
                            today_ohlc = {
                                "open": float(day_open),
                                "high": float(day_high)
                                if day_high
                                else float(
                                    current_price
                                ),  # Use current price if high not available
                                "low": float(day_low)
                                if day_low
                                else float(current_price),  # Use current price if low not available
                                "close": float(day_close),
                            }
                            print(
                                f"✅ Using intraday OHLC from info for {ticker}: O=${day_open:.2f}, H=${today_ohlc['high']:.2f}, L=${today_ohlc['low']:.2f}, C=${day_close:.2f}"
                            )
                        else:
                            print(
                                f"⚠️ No open price in info for {ticker} (got {day_open}), will try intraday history"
                            )
                    except Exception as e:
                        import traceback

                        print(f"⚠️ Could not access info for {ticker}: {e}")
                        traceback.print_exc()

                    # Fallback: try intraday history (1m bars) for today's OHLC
                    if not today_ohlc:
                        try:
                            # Try to get today's intraday data (more accurate than daily bars)
                            with self._suppress_yfinance_output():
                                intraday_hist = stock.history(period="1d", interval="1m")
                            if not intraday_hist.empty:
                                # Get today's data (most recent day)
                                today_ohlc = {
                                    "open": float(
                                        intraday_hist.iloc[0]["Open"]
                                    ),  # First bar of the day
                                    "high": float(
                                        intraday_hist["High"].max()
                                    ),  # Max high of the day
                                    "low": float(intraday_hist["Low"].min()),  # Min low of the day
                                    "close": float(current_price),  # Most recent price
                                }
                                print(
                                    f"✅ Using intraday history OHLC for {ticker}: O=${today_ohlc['open']:.2f}, H=${today_ohlc['high']:.2f}, L=${today_ohlc['low']:.2f}, C=${today_ohlc['close']:.2f}"
                                )
                        except Exception as e:
                            print(f"⚠️ Could not fetch intraday history for {ticker}: {e}")

                    # Final fallback: daily history (may be stale)
                    if not today_ohlc:
                        try:
                            with self._suppress_yfinance_output():
                                daily_hist = stock.history(period="2d", interval="1d")
                            if not daily_hist.empty:
                                latest_day = daily_hist.iloc[-1]
                                today_ohlc = {
                                    "open": float(latest_day["Open"]),
                                    "high": float(latest_day["High"]),
                                    "low": float(latest_day["Low"]),
                                    "close": float(latest_day["Close"]),
                                }
                                print(
                                    f"⚠️ Using daily history OHLC for {ticker} (may be stale): O=${today_ohlc['open']:.2f}, C=${today_ohlc['close']:.2f}"
                                )
                        except Exception as e:
                            print(f"⚠️ Could not fetch daily history for {ticker}: {e}")

                    # Check if market is open
                    market_status = self.get_market_status()
                    is_market_hours = market_status.is_open

                    print(f"✅ Using fast_info for {ticker}: ${price:.2f} (fresh data)")

                    price_data = PriceData(
                        ticker=ticker,
                        price=price,
                        source=source,
                        timestamp=current_time,
                        bid=bid if (bid and bid > 0) else price * 0.999,
                        ask=ask if (ask and ask > 0) else price * 1.001,
                        volume=int(volume) if volume else None,
                        last_trade_price=last_trade_price,
                        last_trade_time=last_trade_time,
                        is_market_hours=bool(is_market_hours),
                        is_fresh=bool(is_fresh),
                        is_inline=bool(is_inline),
                        open=today_ohlc["open"] if today_ohlc else None,
                        high=today_ohlc["high"] if today_ohlc else None,
                        low=today_ohlc["low"] if today_ohlc else None,
                        close=today_ohlc["close"] if today_ohlc else None,
                    )

                    # Store in comprehensive storage system
                    self.storage.store_price_data(ticker, price_data)
                    return price_data
                else:
                    print(f"⚠️ fast_info returned invalid price for {ticker}, trying info...")
            except Exception as e:
                print(f"⚠️ fast_info not available for {ticker}, trying info: {e}")

            # Fallback to info (currentPrice/regularMarketPrice) - more current than history
            # Force fresh info - create new ticker instance to avoid yfinance caching
            try:
                with self._suppress_yfinance_output():
                    info = stock.info
            except Exception:
                # If info access fails, create fresh ticker
                stock = self._ticker(ticker)
                with self._suppress_yfinance_output():
                    info = stock.info
            current_price = (
                info.get("currentPrice")
                or info.get("regularMarketPrice")
                or info.get("regularMarketPreviousClose")
            )

            if current_price and current_price > 0:
                # Use info data (more current than history)
                bid = info.get("bid", current_price * 0.999)
                ask = info.get("ask", current_price * 1.001)
                mid_quote = (bid + ask) / 2 if (bid and ask) else current_price

                market_status = self.get_market_status()
                is_market_hours = market_status.is_open

                # Fetch today's OHLC data - prefer intraday from info, fallback to daily history
                today_ohlc = None
                try:
                    # Use intraday values from info object (more accurate during market hours)
                    # Debug: log what we're getting from info
                    print(
                        f"🔍 Debug {ticker} info values: regularMarketOpen={info.get('regularMarketOpen')}, regularMarketDayHigh={info.get('regularMarketDayHigh')}, regularMarketDayLow={info.get('regularMarketDayLow')}"
                    )

                    day_open = info.get("regularMarketOpen") or info.get("open")
                    day_high = info.get("regularMarketDayHigh") or info.get("dayHigh")
                    day_low = info.get("regularMarketDayLow") or info.get("dayLow")
                    day_close = current_price  # Use current price as today's close (most recent)

                    # If we have at least open, use it (high/low might not be available early in the day)
                    if day_open:
                        today_ohlc = {
                            "open": float(day_open),
                            "high": float(day_high)
                            if day_high
                            else float(current_price),  # Use current price if high not available
                            "low": float(day_low)
                            if day_low
                            else float(current_price),  # Use current price if low not available
                            "close": float(day_close),
                        }
                        print(
                            f"✅ Using intraday OHLC from info for {ticker}: O=${day_open:.2f}, H=${today_ohlc['high']:.2f}, L=${today_ohlc['low']:.2f}, C=${day_close:.2f}"
                        )
                    else:
                        print(
                            f"⚠️ No open price in info for {ticker} (got {day_open}), will try intraday history"
                        )
                except Exception as e:
                    import traceback

                    print(f"⚠️ Could not access info for {ticker}: {e}")
                    traceback.print_exc()

                    # Fallback: try intraday history (1m bars) for today's OHLC
                    if not today_ohlc:
                        try:
                            # Try to get today's intraday data (more accurate than daily bars)
                            with self._suppress_yfinance_output():
                                intraday_hist = stock.history(period="1d", interval="1m")
                            if not intraday_hist.empty:
                                # Get today's data
                                today_ohlc = {
                                    "open": float(
                                        intraday_hist.iloc[0]["Open"]
                                    ),  # First bar of the day
                                    "high": float(
                                        intraday_hist["High"].max()
                                    ),  # Max high of the day
                                    "low": float(intraday_hist["Low"].min()),  # Min low of the day
                                    "close": float(current_price),  # Most recent price
                                }
                                print(
                                    f"✅ Using intraday history OHLC for {ticker}: O=${today_ohlc['open']:.2f}, H=${today_ohlc['high']:.2f}, L=${today_ohlc['low']:.2f}, C=${today_ohlc['close']:.2f}"
                                )
                        except Exception as e:
                            print(f"⚠️ Could not fetch intraday history for {ticker}: {e}")

                    # Final fallback: daily history (may be stale)
                    if not today_ohlc:
                        try:
                            with self._suppress_yfinance_output():
                                daily_hist = stock.history(period="2d", interval="1d")
                            if not daily_hist.empty:
                                latest_day = daily_hist.iloc[-1]
                                today_ohlc = {
                                    "open": float(latest_day["Open"]),
                                    "high": float(latest_day["High"]),
                                    "low": float(latest_day["Low"]),
                                    "close": float(latest_day["Close"]),
                                }
                                print(
                                    f"⚠️ Using daily history OHLC for {ticker} (may be stale): O=${today_ohlc['open']:.2f}, C=${today_ohlc['close']:.2f}"
                                )
                        except Exception as e:
                            print(f"⚠️ Could not fetch daily history for {ticker}: {e}")
                except Exception as e:
                    print(f"⚠️ Could not fetch OHLC for {ticker}: {e}")

                print(f"✅ Using info.currentPrice for {ticker}: ${current_price:.2f} (from info)")

                price_data = PriceData(
                    ticker=ticker,
                    price=current_price,
                    source=PriceSource.LAST_TRADE,
                    timestamp=current_time,
                    bid=bid if bid else current_price * 0.999,
                    ask=ask if ask else current_price * 1.001,
                    volume=info.get("volume"),
                    last_trade_price=current_price,
                    last_trade_time=current_time,
                    is_market_hours=bool(is_market_hours),
                    is_fresh=True,
                    is_inline=True,
                    open=today_ohlc["open"] if today_ohlc else None,
                    high=today_ohlc["high"] if today_ohlc else None,
                    low=today_ohlc["low"] if today_ohlc else None,
                    close=today_ohlc["close"] if today_ohlc else None,
                )

                self.storage.store_price_data(ticker, price_data)
                print(
                    f"✅ Stored fresh price data from info for {ticker}: ${current_price:.2f} at {current_time}"
                )
                return price_data
            else:
                print(f"⚠️ info.currentPrice not available for {ticker}, trying history...")

            # Last resort: try history (but this might be stale)
            print(f"⚠️ WARNING: Using history for {ticker} - this may be stale!")
            with self._suppress_yfinance_output():
                hist = stock.history(period="1d", interval="1m")

            if hist.empty:
                # Try getting just the latest quote
                try:
                    current_price = info.get("currentPrice") or info.get("regularMarketPrice")
                    if current_price:
                        bid = info.get("bid", current_price * 0.999)
                        ask = info.get("ask", current_price * 1.001)
                        mid_quote = (bid + ask) / 2

                        market_status = self.get_market_status()
                        is_market_hours = market_status.is_open

                        price_data = PriceData(
                            ticker=ticker,
                            price=current_price,
                            source=PriceSource.LAST_TRADE,
                            timestamp=current_time,
                            bid=bid,
                            ask=ask,
                            volume=info.get("volume"),
                            last_trade_price=current_price,
                            last_trade_time=current_time,
                            is_market_hours=bool(is_market_hours),
                            is_fresh=True,
                            is_inline=True,
                        )

                        self.storage.store_price_data(ticker, price_data)
                        return price_data
                except Exception as e2:
                    print(f"Could not get price from info: {e2}")

                # Final fallback: 5-day daily history (works from cloud IPs when
                # real-time endpoints are blocked — returns last close, marked stale)
                try:
                    print(f"⚠️ Trying 5-day daily history fallback for {ticker}")
                    daily = self._ticker(ticker).history(period="5d", interval="1d")
                    if not daily.empty:
                        close_price = float(daily["Close"].iloc[-1])
                        if close_price > 0:
                            last_day = daily.index[-1].to_pydatetime()
                            if last_day.tzinfo is None:
                                last_day = last_day.replace(tzinfo=self.tz_utc)
                            else:
                                last_day = last_day.astimezone(self.tz_utc)
                            row = daily.iloc[-1]
                            price_data = PriceData(
                                ticker=ticker,
                                price=close_price,
                                source=PriceSource.LAST_TRADE,
                                timestamp=last_day,
                                bid=close_price * 0.999,
                                ask=close_price * 1.001,
                                volume=int(row.get("Volume", 0)) if row.get("Volume") else None,
                                last_trade_price=close_price,
                                last_trade_time=last_day,
                                is_market_hours=False,
                                is_fresh=False,
                                is_inline=False,
                                open=float(row["Open"]) if not pd.isna(row["Open"]) else None,
                                high=float(row["High"]) if not pd.isna(row["High"]) else None,
                                low=float(row["Low"]) if not pd.isna(row["Low"]) else None,
                                close=close_price,
                            )
                            self.storage.store_price_data(ticker, price_data)
                            print(f"✅ 5-day daily fallback succeeded for {ticker}: ${close_price:.2f} (last close, stale)")
                            return price_data
                except Exception as e3:
                    print(f"⚠️ 5-day daily fallback also failed for {ticker}: {e3}")

                # Stooq fallback: free data provider that doesn't block cloud IPs
                stooq_result = self._fetch_via_stooq(ticker)
                if stooq_result:
                    return stooq_result

                # Last resort: direct HTTP to Yahoo Finance chart API
                chart_result = self._fetch_via_chart_api(ticker)
                if chart_result:
                    return chart_result

                return None

            # Get latest data from history
            latest = hist.iloc[-1]
            last_trade_time = latest.name.to_pydatetime()
            if last_trade_time.tzinfo is None:
                last_trade_time = last_trade_time.replace(tzinfo=self.tz_eastern).astimezone(
                    self.tz_utc
                )
            else:
                last_trade_time = last_trade_time.astimezone(self.tz_utc)

            # Calculate mid-quote if bid/ask available
            bid = info.get("bid", latest["Low"])
            ask = info.get("ask", latest["High"])
            mid_quote = (bid + ask) / 2 if bid and ask else latest["Close"]

            # Determine price source following specification policy
            last_trade_price = latest["Close"]

            # Reference price policy: Last trade if age ≤3s & within ±1% of mid
            age_seconds = (current_time - last_trade_time).total_seconds()
            price_diff_pct = abs(last_trade_price - mid_quote) / mid_quote if mid_quote > 0 else 1.0

            # For stale data (more than 15 minutes old), warn and try to get currentPrice
            if age_seconds > 900:  # 15 minutes
                print(f"⚠️ WARNING: History data for {ticker} is {age_seconds/60:.1f} minutes old!")
                current_price = info.get("currentPrice") or info.get("regularMarketPrice")
                if current_price and current_price > 0:
                    last_trade_price = current_price
                    last_trade_time = current_time  # Use current time for info-based price
                    age_seconds = 0  # Consider it fresh if from info
                    print(
                        f"✅ Using currentPrice from info (${current_price:.2f}) instead of stale history data"
                    )
                else:
                    print(
                        f"❌ ERROR: Cannot get current price for {ticker} - data is {age_seconds/60:.1f} minutes old!"
                    )

            if age_seconds <= 3 and price_diff_pct <= 0.01:
                price = last_trade_price
                source = PriceSource.LAST_TRADE
                is_fresh = True
                is_inline = True
            else:
                price = mid_quote
                source = PriceSource.MID_QUOTE
                is_fresh = age_seconds <= 3
                is_inline = price_diff_pct <= 0.01

            # Check if market is open
            market_status = self.get_market_status()
            is_market_hours = market_status.is_open

            price_data = PriceData(
                ticker=ticker,
                price=price,
                source=source,
                timestamp=current_time,
                bid=bid,
                ask=ask,
                volume=int(latest["Volume"]) if not pd.isna(latest["Volume"]) else None,
                last_trade_price=last_trade_price,
                last_trade_time=last_trade_time,
                is_market_hours=bool(is_market_hours),
                is_fresh=bool(is_fresh),
                is_inline=bool(is_inline),
                open=float(latest["Open"]) if not pd.isna(latest["Open"]) else None,
                high=float(latest["High"]) if not pd.isna(latest["High"]) else None,
                low=float(latest["Low"]) if not pd.isna(latest["Low"]) else None,
                close=float(latest["Close"]) if not pd.isna(latest["Close"]) else None,
            )

            # Store in comprehensive storage system
            self.storage.store_price_data(ticker, price_data)

            return price_data

        except YFRateLimitError:
            self.last_error_kind = "provider_unavailable"
            print(f"⚠️ Yahoo Finance rate limit hit for {ticker}")
        except Exception as e:
            print(f"⚠️ yfinance exception for {ticker}: {type(e).__name__}: {e}")
            err_str = str(e).lower()
            if "rate" in err_str or "too many" in err_str or "429" in err_str:
                self.last_error_kind = "provider_unavailable"

        # All yfinance paths failed — try alternative sources
        print(f"⚠️ All yfinance paths failed for {ticker}, trying alternatives")
        stooq_result = self._fetch_via_stooq(ticker)
        if stooq_result:
            return stooq_result
        chart_result = self._fetch_via_chart_api(ticker)
        if chart_result:
            return chart_result
        return None

    def get_market_status(self) -> MarketStatus:
        """Get current market status."""
        try:
            # Get market calendar for today
            now_eastern = datetime.now(self.tz_eastern)
            today = now_eastern.date()

            # Market hours: 9:30 AM to 4:00 PM ET, Monday-Friday
            market_open = now_eastern.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = now_eastern.replace(hour=16, minute=0, second=0, microsecond=0)

            # Check if it's a weekday
            is_weekday = now_eastern.weekday() < 5

            # Check if current time is within market hours
            is_open = is_weekday and market_open <= now_eastern <= market_close

            # Calculate next open/close
            next_open = None
            next_close = None

            if not is_open:
                if now_eastern < market_open and is_weekday:
                    # Market opens today
                    next_open = market_open
                    next_close = market_close
                else:
                    # Market closed, find next trading day
                    next_trading_day = self._get_next_trading_day(today)
                    next_open = self.tz_eastern.localize(
                        datetime.combine(
                            next_trading_day, datetime.min.time().replace(hour=9, minute=30)
                        )
                    )
                    next_close = self.tz_eastern.localize(
                        datetime.combine(
                            next_trading_day, datetime.min.time().replace(hour=16, minute=0)
                        )
                    )

            return MarketStatus(
                is_open=is_open, next_open=next_open, next_close=next_close, timezone="US/Eastern"
            )

        except Exception as e:
            print(f"Error getting market status: {e}")
            return MarketStatus(is_open=False, timezone="US/Eastern")

    def validate_price(
        self, price_data: PriceData, allow_after_hours: bool = False
    ) -> Dict[str, Any]:
        """Validate price data for trading decisions."""
        validation_result = {"valid": True, "warnings": [], "rejections": []}

        # Check if market is open (respect after-hours setting)
        if not price_data.is_market_hours:
            if not allow_after_hours:
                validation_result["valid"] = False
                validation_result["rejections"].append(
                    "Market is closed - after-hours trading disabled"
                )
            else:
                validation_result["warnings"].append("Trading after market hours")

        # Check if price is fresh (within 3 seconds)
        if not price_data.is_fresh:
            validation_result["warnings"].append("Price data is stale (>3 seconds old)")

        # Check if price is inline with mid-quote
        if not price_data.is_inline:
            validation_result["warnings"].append("Price deviates >1% from mid-quote")

        # Check for outlier prices (simplified - would need historical data for proper implementation)
        if price_data.price <= 0:
            validation_result["valid"] = False
            validation_result["rejections"].append("Invalid price (≤0)")

        # Check for extreme price movements (would need volatility calculation)
        # This is a simplified check - in production, you'd calculate 1-min volatility
        if price_data.price > 10000 or price_data.price < 0.01:
            validation_result["warnings"].append("Extreme price detected")

        return validation_result

    def get_reference_price(self, ticker: str) -> Optional[PriceData]:
        """Get reference price following the specification policy."""
        if self._deterministic_guard(ticker):
            return None
        price_data = self.get_price(ticker)
        if not price_data:
            return None

        # Apply reference price policy from specification
        # Reference price: Last trade (if age ≤3s & within ±1% of mid); otherwise mid-quote
        if (
            price_data.source == PriceSource.LAST_TRADE
            and price_data.is_fresh
            and price_data.is_inline
        ):
            return price_data

        # If last trade doesn't meet criteria, use mid-quote
        if price_data.bid and price_data.ask:
            mid_price = (price_data.bid + price_data.ask) / 2
            return PriceData(
                ticker=ticker,
                price=mid_price,
                source=PriceSource.MID_QUOTE,
                timestamp=price_data.timestamp,
                bid=price_data.bid,
                ask=price_data.ask,
                volume=price_data.volume,
                last_trade_price=price_data.last_trade_price,
                last_trade_time=price_data.last_trade_time,
                is_market_hours=price_data.is_market_hours,
                is_fresh=price_data.is_fresh,
                is_inline=price_data.is_inline,
            )

        return price_data

    def _is_cache_valid(self, price_data: PriceData) -> bool:
        """Check if cached price data is still valid."""
        age_seconds = (datetime.now(self.tz_utc) - price_data.timestamp).total_seconds()
        if age_seconds > self.cache_ttl:
            print(f"⚠️ Cache invalid: data is {age_seconds:.1f} seconds old")
            return False
        return True

    def get_current_quote(self, ticker: str) -> Optional[PriceData]:
        """Get the most current quote available, bypassing cache for fresh data."""
        if self._deterministic_guard(ticker):
            return None
        try:
            stock = self._ticker(ticker)
            current_time = datetime.now(self.tz_utc)

            # Try fast_info first (most current)
            try:
                with self._suppress_yfinance_output():
                    fast_info = stock.fast_info
                current_price = fast_info.get("lastPrice") or fast_info.get("regularMarketPrice")
                if current_price:
                    bid = fast_info.get("bid", current_price * 0.999)
                    ask = fast_info.get("ask", current_price * 1.001)

                    market_status = self.get_market_status()

                    return PriceData(
                        ticker=ticker,
                        price=current_price,
                        source=PriceSource.LAST_TRADE,
                        timestamp=current_time,
                        bid=bid,
                        ask=ask,
                        volume=fast_info.get("regularMarketVolume"),
                        last_trade_price=current_price,
                        last_trade_time=current_time,
                        is_market_hours=market_status.is_open,
                        is_fresh=True,
                        is_inline=True,
                    )
            except Exception:
                pass

            # Fallback to info
            with self._suppress_yfinance_output():
                info = stock.info
            current_price = (
                info.get("currentPrice")
                or info.get("regularMarketPrice")
                or info.get("regularMarketPreviousClose")
            )
            if current_price:
                bid = info.get("bid", current_price * 0.999)
                ask = info.get("ask", current_price * 1.001)

                market_status = self.get_market_status()

                return PriceData(
                    ticker=ticker,
                    price=current_price,
                    source=PriceSource.LAST_TRADE,
                    timestamp=current_time,
                    bid=bid,
                    ask=ask,
                    volume=info.get("volume"),
                    last_trade_price=current_price,
                    last_trade_time=current_time,
                    is_market_hours=market_status.is_open,
                    is_fresh=True,
                    is_inline=True,
                )

            # Last resort: use get_price which will try history
            return self.get_price(ticker)

        except Exception as e:
            print(f"Error getting current quote for {ticker}: {e}")
            return None

    def get_historical_data(
        self, ticker: str, start_date: datetime, end_date: datetime, market_hours_only: bool = False
    ) -> List[PriceData]:
        """Get historical price data for simulation and backtesting."""
        return self.storage.get_historical_data(ticker, start_date, end_date, market_hours_only)

    def get_trading_day_data(
        self, ticker: str, days: int = 5, include_after_hours: bool = False
    ) -> List[PriceData]:
        """Get data for last N trading days."""
        return self.storage.get_trading_day_data(ticker, days, include_after_hours)

    def get_volatility(self, ticker: str, window_minutes: int = 60) -> float:
        """Get volatility for a ticker."""
        return self.storage.get_volatility(ticker, window_minutes)

    def get_simulation_data(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        include_after_hours: bool = False,
    ) -> SimulationData:
        """Get comprehensive data for simulation and backtesting."""
        return self.storage.get_simulation_data(ticker, start_date, end_date, include_after_hours)

    def fetch_historical_data(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        intraday_interval_minutes: int = 30,
    ) -> List[PriceData]:
        """Fetch historical data from yfinance and store it."""
        if self._deterministic_guard(ticker):
            return []
        try:
            # Validate input parameters
            if not ticker or not isinstance(ticker, str):
                raise ValueError(f"Invalid ticker: {ticker}")

            # Ensure both dates are timezone-aware for comparison
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=self.tz_utc)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=self.tz_utc)

            if start_date >= end_date:
                raise ValueError(f"Start date {start_date} must be before end date {end_date}")

            # Convert to yfinance format
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            # yfinance intraday data limits:
            #   1m / 5m / 15m / 30m : last 60 days only
            #   1h                   : last 730 days
            #   daily (1440 min)    : full history
            # Route to daily synthetic data whenever the span exceeds what yfinance supports
            # for the requested interval, or when daily resolution is explicitly requested.
            days_diff = (end_date - start_date).days

            intraday_limit_days = {
                1: 7, 5: 60, 15: 60, 30: 60, 60: 730,
            }
            limit_days = intraday_limit_days.get(intraday_interval_minutes, 60)

            if intraday_interval_minutes >= 1440 or days_diff > limit_days:
                print(
                    f"Span {days_diff}d exceeds {limit_days}d limit for {intraday_interval_minutes}min "
                    f"— using daily data with synthetic intraday points"
                )
                return self._fetch_daily_with_synthetic_intraday(
                    ticker, start_date, end_date, intraday_interval_minutes
                )

            # Within supported range — try minute data
            if days_diff <= 7:
                interval = "1m"  # 1-minute data for short periods
            else:
                # For longer recent periods, use chunked minute data
                return self._fetch_chunked_minute_data(
                    ticker, start_date, end_date, intraday_interval_minutes
                )

            # Fetch data with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    stock = self._ticker(ticker)
                    with self._suppress_yfinance_output():
                        hist = stock.history(start=start_str, end=end_str, interval=interval)
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise Exception(
                            f"Failed to fetch data after {max_retries} attempts: {str(e)}"
                        )
                    print(f"Attempt {attempt + 1} failed, retrying...: {str(e)}")
                    time.sleep(1)  # Wait 1 second before retry

            if hist.empty:
                print(f"Warning: No data returned for {ticker} from {start_str} to {end_str}")
                return []

            # Convert to PriceData objects
            price_data_list = []
            for timestamp, row in hist.iterrows():
                # Convert timestamp to UTC
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=self.tz_eastern).astimezone(self.tz_utc)
                else:
                    timestamp = timestamp.astimezone(self.tz_utc)

                # Calculate mid-quote
                mid_quote = (row["High"] + row["Low"]) / 2

                # Determine if market hours
                is_market_hours = self.storage.is_market_hours(timestamp)

                if interval == "1m":
                    # For minute data, create one PriceData object
                    # For minute data, use close as both bid and ask (no spread)
                    bid_price = row["Close"]
                    ask_price = row["Close"]
                    mid_quote = row["Close"]

                    price_data = PriceData(
                        ticker=ticker,
                        price=mid_quote,  # Use mid-quote for trading calculations
                        source=PriceSource.LAST_TRADE,
                        timestamp=timestamp,
                        bid=bid_price,
                        ask=ask_price,
                        volume=int(row["Volume"]) if not pd.isna(row["Volume"]) else None,
                        last_trade_price=row["Close"],
                        last_trade_time=timestamp,
                        is_market_hours=bool(is_market_hours),
                        is_fresh=True,  # Historical data is considered fresh
                        is_inline=True,  # Historical data is considered inline
                        # OHLC data for daily bars
                        open=row["Open"],
                        high=row["High"],
                        low=row["Low"],
                        close=row["Close"],
                    )
                    price_data_list.append(price_data)
                    self.storage.store_price_data(ticker, price_data)
                else:
                    # For daily data, create multiple intraday points to simulate intraday trading
                    # Create configurable evaluation points per day (default: every 30 minutes)
                    # Market hours: 9:30 AM - 4:00 PM ET (6.5 hours = 390 minutes)
                    # Default: every 30 minutes = 13 points per day
                    # Use the provided intraday_interval_minutes parameter
                    # Use the provided intraday_interval_minutes parameter
                    intraday_times = []

                    # Generate times every N minutes from 9:30 AM to 4:00 PM
                    current_hour, current_minute = 9, 30
                    while current_hour < 16 or (current_hour == 16 and current_minute == 0):
                        intraday_times.append((current_hour, current_minute))
                        current_minute += intraday_interval_minutes
                        if current_minute >= 60:
                            current_hour += 1
                            current_minute -= 60

                    print(
                        f"DEBUG: Generated {len(intraday_times)} intraday times: {intraday_times[:5]}..."
                    )

                    for hour, minute in intraday_times:
                        # Create timestamp for this intraday point
                        # Convert to Eastern time first, then set the hour/minute, then convert back to UTC
                        et_timestamp = timestamp.astimezone(self.tz_eastern)
                        intraday_timestamp = et_timestamp.replace(
                            hour=hour, minute=minute, second=0, microsecond=0
                        )
                        intraday_timestamp = intraday_timestamp.astimezone(self.tz_utc)

                        # Skip if not during market hours (weekends, holidays, outside trading hours)
                        if not self.storage.is_market_hours(intraday_timestamp):
                            continue

                        # Simulate price movement within the day using OHLC data
                        # Use a simple linear interpolation between open and close
                        progress = (hour - 9.5) / 6.5  # Progress from 9:30 to 4:00
                        progress = max(0, min(1, progress))  # Clamp between 0 and 1

                        # Interpolate price between open and close
                        simulated_price = row["Open"] + (row["Close"] - row["Open"]) * progress

                        # Create realistic bid/ask spread (0.1% of price)
                        spread = simulated_price * 0.001
                        bid_price = simulated_price - spread / 2
                        ask_price = simulated_price + spread / 2
                        mid_quote = simulated_price

                        # Distribute volume across intraday points
                        intraday_volume = (
                            int(row["Volume"] / len(intraday_times))
                            if not pd.isna(row["Volume"])
                            else None
                        )

                        price_data = PriceData(
                            ticker=ticker,
                            price=mid_quote,  # Use mid-quote for trading calculations
                            source=PriceSource.LAST_TRADE,
                            timestamp=intraday_timestamp,
                            bid=bid_price,  # Realistic bid price
                            ask=ask_price,  # Realistic ask price
                            volume=intraday_volume,
                            last_trade_price=simulated_price,
                            last_trade_time=intraday_timestamp,
                            is_market_hours=True,  # All intraday points are during market hours
                            is_fresh=True,
                            is_inline=True,
                            # OHLC data for daily bars (same for all intraday points)
                            open=row["Open"],
                            high=row["High"],
                            low=row["Low"],
                            close=row["Close"],
                        )
                        price_data_list.append(price_data)
                        self.storage.store_price_data(ticker, price_data)

            # Validate data quality
            validator = DataValidator()
            validation_issues = validator.validate_price_data_series(price_data_list)

            if validation_issues:
                quality_summary = validator.get_quality_summary(validation_issues)
                print(f"Data quality validation for {ticker}:")
                print(f"  Quality score: {quality_summary['quality_score']}/100")
                print(
                    f"  Issues: {quality_summary['errors']} errors, {quality_summary['warnings']} warnings, {quality_summary['info']} info"
                )

                # Log critical issues
                for issue in validation_issues:
                    if issue.severity == "error":
                        print(f"  ERROR: {issue.message}")
                    elif issue.severity == "warning":
                        print(f"  WARNING: {issue.message}")

            return price_data_list

        except Exception as e:
            print(f"Error fetching historical data for {ticker}: {e}")
            return []

    def _fetch_chunked_minute_data(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        intraday_interval_minutes: int = 30,
    ) -> List[PriceData]:
        """Fetch minute-by-minute data in chunks for periods >7 days."""
        print(f"Fetching chunked minute data for {ticker} from {start_date} to {end_date}")

        all_price_data = []
        current_start = start_date

        # Process in 7-day chunks
        chunk_days = 7
        chunk_delta = timedelta(days=chunk_days)

        while current_start < end_date:
            current_end = min(current_start + chunk_delta, end_date)

            print(f"Fetching chunk: {current_start} to {current_end}")

            try:
                # Fetch this chunk
                chunk_data = self._fetch_single_chunk(
                    ticker, current_start, current_end, intraday_interval_minutes
                )
                all_price_data.extend(chunk_data)

                print(f"  Got {len(chunk_data)} data points")

            except Exception as e:
                print(f"  Error fetching chunk {current_start} to {current_end}: {e}")
                # Continue with next chunk instead of failing completely

            # Move to next chunk
            current_start = current_end

        print(f"Total chunked data points: {len(all_price_data)}")
        return all_price_data

    def _fetch_single_chunk(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        intraday_interval_minutes: int = 30,
    ) -> List[PriceData]:
        """Fetch a single chunk of data - tries minute data first, falls back to daily."""
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        stock = self._ticker(ticker)

        # Try minute data first (only available for last ~7 days)
        hist = stock.history(start=start_str, end=end_str, interval="1m")

        # If minute data is empty, fall back to daily data with synthetic intraday points
        if hist.empty:
            print(f"  No 1m data for {start_str} to {end_str}, falling back to daily data")
            hist = stock.history(start=start_str, end=end_str, interval="1d")
            if hist.empty:
                return []
            return self._generate_intraday_from_daily(ticker, hist, intraday_interval_minutes)

        price_data_list = []

        # Convert to PriceData objects
        for timestamp, row in hist.iterrows():
            # Convert timestamp to UTC
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=self.tz_utc)
            else:
                timestamp = timestamp.astimezone(self.tz_utc)

            # Check if this is during market hours
            is_market_hours = self.storage.is_market_hours(timestamp)

            # For minute data, use close as both bid and ask (no spread)
            bid_price = row["Close"]
            ask_price = row["Close"]
            mid_quote = row["Close"]

            price_data = PriceData(
                ticker=ticker,
                price=mid_quote,  # Use mid-quote for trading calculations
                source=PriceSource.LAST_TRADE,
                timestamp=timestamp,
                bid=bid_price,
                ask=ask_price,
                volume=int(row["Volume"]) if not pd.isna(row["Volume"]) else None,
                last_trade_price=row["Close"],
                last_trade_time=timestamp,
                is_market_hours=bool(is_market_hours),
                is_fresh=True,  # Historical data is considered fresh
                is_inline=True,  # Historical data is considered inline
                # OHLC data for daily bars
                open=row["Open"],
                high=row["High"],
                low=row["Low"],
                close=row["Close"],
            )
            price_data_list.append(price_data)
            self.storage.store_price_data(ticker, price_data)

        return price_data_list

    def _fetch_daily_with_synthetic_intraday(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        intraday_interval_minutes: int = 30,
    ) -> List[PriceData]:
        """Fetch daily data and generate synthetic intraday points for historical simulations."""
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        print(f"Fetching daily data for {ticker} from {start_str} to {end_str}")

        stock = self._ticker(ticker)
        hist = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                hist = stock.history(start=start_str, end=end_str, interval="1d")
                if not hist.empty:
                    break
                if attempt < max_retries - 1:
                    print(f"Daily fetch returned empty for {ticker}, retrying ({attempt + 1}/{max_retries})...")
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                print(f"Daily fetch error for {ticker} (attempt {attempt + 1}): {e}, retrying...")

        if hist is None or hist.empty:
            # Fallback: try fetching by period instead of explicit date range.
            # Some yfinance versions / Yahoo Finance states handle period better.
            days_diff = (end_date - start_date).days
            if days_diff >= 365:
                period = "2y"
            elif days_diff >= 180:
                period = "1y"
            elif days_diff >= 90:
                period = "6mo"
            else:
                period = "3mo"
            print(f"Retrying {ticker} with period={period} fallback (start/end fetch returned empty)...")
            try:
                stock2 = self._ticker(ticker)
                hist = stock2.history(period=period, interval="1d")
                if not hist.empty:
                    # Trim to requested range
                    if hist.index.tzinfo is None:
                        hist.index = hist.index.tz_localize("UTC")
                    else:
                        hist.index = hist.index.tz_convert("UTC")
                    hist = hist[(hist.index >= start_date) & (hist.index <= end_date)]
                    print(f"Period fallback succeeded: {len(hist)} rows after trimming")
            except Exception as e:
                print(f"Period fallback also failed for {ticker}: {e}")
                hist = None

        if hist is None or hist.empty:
            print(f"Warning: No daily data returned for {ticker}")
            return []

        print(f"Got {len(hist)} daily bars, generating synthetic intraday points...")
        return self._generate_intraday_from_daily(ticker, hist, intraday_interval_minutes)

    def _generate_intraday_from_daily(
        self,
        ticker: str,
        daily_hist,
        intraday_interval_minutes: int = 30,
    ) -> List[PriceData]:
        """Generate synthetic intraday data points from daily OHLC data.

        This creates realistic intraday price movements by interpolating between
        Open, High, Low, and Close prices throughout the trading day.
        """
        price_data_list = []

        # For daily (or larger) resolution, use a single price point per day at close.
        # The minute-increment loop below would produce invalid times (minute > 59) for
        # intervals >= a full trading session (390 minutes = 9:30→16:00).
        if intraday_interval_minutes >= 390:
            for timestamp, row in daily_hist.iterrows():
                close_price = row["Close"]
                volume = int(row["Volume"]) if not pd.isna(row["Volume"]) else 0
                if timestamp.tzinfo is None:
                    day_date = timestamp.replace(tzinfo=self.tz_utc)
                else:
                    day_date = timestamp.astimezone(self.tz_utc)
                if day_date.weekday() >= 5:
                    continue
                et_close = day_date.astimezone(self.tz_eastern).replace(
                    hour=16, minute=0, second=0, microsecond=0
                )
                utc_close = et_close.astimezone(self.tz_utc)
                price_point = PriceData(
                    ticker=ticker,
                    price=float(close_price),
                    source=PriceSource.LAST_TRADE,
                    timestamp=utc_close,
                    volume=volume,
                    last_trade_price=float(close_price),
                    last_trade_time=utc_close,
                    is_market_hours=True,
                    is_fresh=True,
                    is_inline=True,
                    open=float(row["Open"]) if not pd.isna(row["Open"]) else None,
                    high=float(row["High"]) if not pd.isna(row["High"]) else None,
                    low=float(row["Low"]) if not pd.isna(row["Low"]) else None,
                    close=float(close_price),
                )
                price_data_list.append(price_point)
                self.storage.store_price_data(ticker, price_point)
            return price_data_list

        # Generate intraday times (9:30 AM to 4:00 PM ET) for sub-daily intervals
        intraday_times = []
        total_minutes = 9 * 60 + 30  # start at 9:30
        end_minutes = 16 * 60         # end at 16:00
        while total_minutes <= end_minutes:
            intraday_times.append((total_minutes // 60, total_minutes % 60))
            total_minutes += intraday_interval_minutes

        for timestamp, row in daily_hist.iterrows():
            # Get OHLC for the day
            open_price = row["Open"]
            high_price = row["High"]
            low_price = row["Low"]
            close_price = row["Close"]
            volume = int(row["Volume"]) if not pd.isna(row["Volume"]) else 0

            # Convert timestamp to timezone-aware
            if timestamp.tzinfo is None:
                day_date = timestamp.replace(tzinfo=self.tz_utc)
            else:
                day_date = timestamp.astimezone(self.tz_utc)

            # Skip weekends
            if day_date.weekday() >= 5:
                continue

            # Generate intraday points with realistic price movement
            # Pattern: Open -> High -> Low -> Close (simplified but realistic)
            num_points = len(intraday_times)
            volume_per_point = volume // num_points if num_points > 0 else 0

            for i, (hour, minute) in enumerate(intraday_times):
                # Create timestamp in Eastern time, then convert to UTC
                et_timestamp = day_date.astimezone(self.tz_eastern)
                intraday_timestamp = et_timestamp.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
                intraday_timestamp = intraday_timestamp.astimezone(self.tz_utc)

                # Calculate interpolated price based on position in day
                # First quarter: Open to High
                # Second quarter: High
                # Third quarter: High to Low
                # Fourth quarter: Low to Close
                progress = i / max(num_points - 1, 1)

                if progress < 0.25:
                    # Open to High
                    t = progress / 0.25
                    price = open_price + t * (high_price - open_price)
                elif progress < 0.5:
                    # Around High
                    t = (progress - 0.25) / 0.25
                    price = high_price - t * (high_price - low_price) * 0.3
                elif progress < 0.75:
                    # High to Low
                    t = (progress - 0.5) / 0.25
                    price = high_price - t * (high_price - low_price)
                else:
                    # Low to Close
                    t = (progress - 0.75) / 0.25
                    price = low_price + t * (close_price - low_price)

                price_data = PriceData(
                    ticker=ticker,
                    price=price,
                    source=PriceSource.LAST_TRADE,
                    timestamp=intraday_timestamp,
                    bid=price,
                    ask=price,
                    volume=volume_per_point,
                    last_trade_price=price,
                    last_trade_time=intraday_timestamp,
                    is_market_hours=True,
                    is_fresh=True,
                    is_inline=True,
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                )
                price_data_list.append(price_data)
                self.storage.store_price_data(ticker, price_data)

        print(f"  Generated {len(price_data_list)} synthetic intraday points from {len(daily_hist)} daily bars")
        return price_data_list

    def _get_next_trading_day(self, date) -> datetime:
        """Get the next trading day (Monday-Friday)."""
        next_day = date + timedelta(days=1)
        while next_day.weekday() >= 5:  # Skip weekends
            next_day += timedelta(days=1)
        return next_day
