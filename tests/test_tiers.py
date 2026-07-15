from kalshi_data.tiers import classify


def test_parlays_excluded_regardless_of_category():
    assert classify("KXMVESPORTSMULTIGAMEEXTENDED-S123", "Economics") == "excluded"


def test_sports_and_crypto_are_instrumentation():
    assert classify("KXNFLGAME", "Sports") == "instrumentation"
    assert classify("KXBTCD", "Crypto") == "instrumentation"


def test_deployment_categories():
    assert classify("KXCPI", "Economics") == "deployment"
    assert classify("KXHIGHNY", "Climate and Weather") == "deployment"
    assert classify("KXFED", "Financials") == "deployment"
    assert classify("KXPRES", "Politics") == "deployment"


def test_amended_deployment_categories():
    assert classify("KXSENATE", "Elections") == "deployment"
    assert classify("KXWTI", "Commodities") == "deployment"
    assert classify("KXFLU", "Health") == "deployment"


def test_unknown_category_goes_to_review_not_deployment():
    assert classify("KXOSCAR", "Entertainment") == "review"
    assert classify("KXMENTION", "Mentions") == "review"
    assert classify("KXFOO", None) == "review"
