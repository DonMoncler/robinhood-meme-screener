"""
Apify Twitter (X) scraper client -- Tweet Scraper V2 (apidojo/tweet-scraper).
Docs: https://apify.com/apidojo/tweet-scraper

NOT free: needs an Apify account with a payment method (usage-based,
~$0.40 per 1,000 tweets, 50-tweet minimum per search query). No API
access on Apify's free plan for this actor.
"""
import os
import requests

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")
ACTOR_ID = "apidojo~tweet-scraper"
RUN_SYNC_URL = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"


def search_tweets(search_terms, max_items=100, sort="Latest"):
    """
    search_terms: list of query strings (batch multiple cashtags into ONE
    OR-joined query to minimize cost, e.g. ["($CASHCAT OR $DOGH OR $FOO) lang:en"]).
    Returns a list of raw tweet dicts from the actor's dataset.
    """
    if not APIFY_API_TOKEN:
        raise RuntimeError("APIFY_API_TOKEN not set")

    payload = {
        "searchTerms": search_terms,
        "maxItems": max_items,
        "sort": sort,
        "tweetLanguage": "en",
    }
    r = requests.post(
        RUN_SYNC_URL,
        params={"token": APIFY_API_TOKEN},
        json=payload,
        timeout=120,
    )
    r.raise_for_status()
    return r.json()
