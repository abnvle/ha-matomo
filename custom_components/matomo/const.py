"""Constants for the Matomo Analytics integration."""

from datetime import timedelta

DOMAIN = "matomo"

CONF_URL = "url"
CONF_TOKEN = "token_auth"
CONF_SITE_ID = "site_id"
CONF_SITE_NAME = "site_name"
CONF_INCLUDE_AGGREGATE = "include_aggregate"

DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)
LIVE_SCAN_INTERVAL = timedelta(seconds=60)

ATTR_NB_UNIQ_VISITORS = "nb_uniq_visitors"
ATTR_NB_VISITS = "nb_visits"
ATTR_NB_ACTIONS = "nb_actions"
ATTR_NB_PAGEVIEWS = "nb_pageviews"
ATTR_BOUNCE_COUNT = "bounce_count"
ATTR_SUM_VISIT_LENGTH = "sum_visit_length"
ATTR_NB_USERS = "nb_users"
