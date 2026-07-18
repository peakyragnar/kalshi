import polars as pl

from kalshi_data.core.tiers import apply_current_tiers, classify


def test_parlays_excluded_regardless_of_category():
    assert classify("KXMVESPORTSMULTIGAMEEXTENDED-S123", "Economics") == "excluded"


def test_sports_and_crypto_are_instrumentation():
    assert classify("KXNFLGAME", "Sports") == "instrumentation"
    assert classify("KXBTCD", "Crypto") == "instrumentation"


def test_sports_series_mislabeled_in_other_categories_are_instrumentation():
    assert classify("KXMLBMENTION", "Mentions", "MLB Announcers", ["Sports"]) == "instrumentation"
    assert classify("KXSUPERBOWLAD", "Companies", "Super Bowl ads") == "instrumentation"
    assert classify("KXLEBRONMENTION", "Mentions", "Lebron James Mention") == "instrumentation"


def test_crypto_series_mislabeled_in_other_categories_are_instrumentation():
    assert classify("KXBTCRESERVE", "Politics", "Will the US create a Bitcoin reserve?") == "instrumentation"
    assert classify("KXCOINBASEVOLUME", "Companies", "Coinbase trading volume") == "instrumentation"
    assert classify("KXSTABLECOIN", "Financials", "Stablecoin market cap") == "instrumentation"


def test_crypto_words_do_not_recreate_substring_false_positives():
    assert classify("KXDOGESAVINGS", "Politics", "DOGE government savings") == "deployment"
    assert classify("KXCRYPTOSPORIDIUM", "Health", "Cryptosporidium cases") == "deployment"


def test_sports_words_do_not_recreate_substring_false_positives():
    assert classify("KXALBUM", "Entertainment", "NBA Youngboy album release") == "deployment"
    assert classify("KXCOACHELLA", "Entertainment", "Coachella lineup") == "deployment"
    assert classify("KXFLIGHTJFK", "Transportation", "JFK flight count") == "deployment"
    assert classify("KXMICHTEMP", "Climate and Weather", "Lake Michigan temperature") == "deployment"
    assert classify("KXMICHELINBOS", "Politics", "Michelin star Boston") == "deployment"


def test_deployment_categories():
    assert classify("KXCPI", "Economics") == "deployment"
    assert classify("KXHIGHNY", "Climate and Weather") == "deployment"
    assert classify("KXFED", "Financials") == "deployment"
    assert classify("KXPRES", "Politics") == "deployment"


def test_amended_deployment_categories():
    assert classify("KXSENATE", "Elections") == "deployment"
    assert classify("KXWTI", "Commodities") == "deployment"
    assert classify("KXFLU", "Health") == "deployment"


def test_every_non_sports_non_crypto_category_is_deployment():
    assert classify("KXOSCAR", "Entertainment") == "deployment"
    assert classify("KXMENTION", "Mentions") == "deployment"
    assert classify("KXSOCIAL", "Social") == "deployment"
    assert classify("KXEDUCATION", "Education") == "deployment"
    assert classify("KXFLIGHTJFK", "Transportation") == "deployment"
    assert classify("KXFOO", None) == "deployment"


def test_current_catalog_tier_overrides_historical_raw_tier():
    markets = pl.DataFrame({
        "ticker": ["M1", "M2"],
        "series_ticker": ["SPORT-LABEL", "NORMAL"],
        "tier": ["deployment", "deployment"],
    })
    series = pl.DataFrame({
        "ticker": ["SPORT-LABEL", "NORMAL"],
        "tier": ["instrumentation", "deployment"],
    })

    out = apply_current_tiers(markets, series).sort("ticker")

    assert out["tier"].to_list() == ["instrumentation", "deployment"]
