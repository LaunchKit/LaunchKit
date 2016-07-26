#
# Copyright 2016 Cluster Labs, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from django.conf.urls import patterns
from django.conf.urls import url

from backend.lk.views import apps
from backend.lk.views import appstore
from backend.lk.views import auth
from backend.lk.views import config
from backend.lk.views import debug
from backend.lk.views import itunes
from backend.lk.views import reviews
from backend.lk.views import screenshots
from backend.lk.views import sdk
from backend.lk.views import slack
from backend.lk.views import tracking
from backend.lk.views import twitter
from backend.lk.views import user_intelligence
from backend.lk.views import websites


urlpatterns = patterns('',
    url(r'^signup$', auth.signup),

    url(r'^oauth2/auth$', auth.oauth2_auth_view),
    url(r'^oauth2/token$', auth.oauth2_token_view),
    url(r'^oauth2/invalidate_token$', auth.oauth2_invalidate_token_view),

    url(r'^reset_password$', auth.reset_password_view),
    url(r'^reset_password/finish$', auth.reset_password_finish_view),

    url(r'^verify_email$', auth.verify_email_view),
    url(r'^unsubscribe$', auth.unsubscribe_view),

    url(r'^user$', auth.user),
    url(r'^user/details$', auth.user_details),

    url(r'^user/emails/request_verification$', auth.request_verification_email),
    url(r'^user/emails$', auth.emails_view),
    url(r'^user/emails/set_primary$', auth.email_set_primary_view),
    url(r'^user/emails/delete$', auth.email_delete_view),

    url(r'^user/delete$', auth.delete_account_view),

    url(r'^users/(?P<user_id>[\w-]{11})$', auth.user_by_id),

    # SALES REPORTS AND ITUNES CONNECT

    url(r'^itunes/connect$', itunes.connect_itunes_view),
    url(r'^itunes/disconnect$', itunes.disconnect_itunes_view),
    url(r'^itunes/vendors$', itunes.get_vendors_view),
    url(r'^itunes/choose_vendor$', itunes.choose_vendor_view),
    url(r'^itunes/sales_metrics$', itunes.get_sales_metrics_view),
    url(r'^itunes/subscriptions$', itunes.subscriptions_view),

    # NOTE: This word is 11 characters long.
    url(r'^itunes/subscriptions/unsubscribe$', itunes.subscription_unsubscribe_token_view),
    url(r'^itunes/subscriptions/(?P<subscription_id>[\w-]{11})/delete$', itunes.subscription_delete_view),


    # SLACK

    url(r'^slack$', slack.connect_slack_view),
    url(r'^slack/channels$', slack.slack_channels_view),
    url(r'^slack/usage$', slack.slack_usage_view),
    url(r'^slack/disconnect$', slack.slack_disconnect_view),

    # TWITTER

    url(r'^twitter/connect$', twitter.connect_twitter_view),
    url(r'^twitter/finish$', twitter.connect_twitter_finish_view),
    url(r'^twitter/tweet_review$', twitter.tweet_review),
    url(r'^twitter/connections$', twitter.get_twitter_app_connections_view),
    url(r'^twitter/connect_app$', twitter.connect_app_view),
    url(r'^twitter/disconnect_app$', twitter.disconnect_app_view),

    # APP STORE

    url(r'^appstore/(?P<country>[a-z]{2})/(?P<app_id>\d+)$', appstore.summary_view),

    # MY APPS

    url(r'^apps$', apps.apps_view),
    url(r'^apps/(?P<country>[a-z]{2})/(?P<app_id>[\w-]{11})/delete$', apps.app_delete_view),

    # REVIEWS AND SUBSCRIPTIONS

    url(r'^reviews$', reviews.reviews_view),
    url(r'^reviews/(?P<review_id>[\w-]{11})$', reviews.review_view),
    url(r'^reviews/subscriptions$', reviews.subscriptions_view),

    # NOTE: This word is 11 characters long.
    url(r'^reviews/subscriptions/unsubscribe$', reviews.subscription_unsubscribe_token_view),

    url(r'^reviews/subscriptions/(?P<subscription_id>[\w-]{11})$', reviews.subscription_view),
    url(r'^reviews/subscriptions/(?P<subscription_id>[\w-]{11})/delete$', reviews.subscription_delete_view),

    # SCREENSHOTS

    url(r'^screenshot_images$', screenshots.screenshot_images_view),
    url(r'^background_images$', screenshots.background_images_view),
    url(r'^website_icon_images$', screenshots.website_icon_images_view),
    url(r'^website_logo_images$', screenshots.website_logo_images_view),
    url(r'^website_background_images$', screenshots.website_background_images_view),
    url(r'^website_screenshot_images$', screenshots.website_screenshot_images_view),

    url(r'^screenshot_sets$', screenshots.screenshot_sets_view),
    url(r'^screenshot_sets/(?P<set_id>[\w-]{11})$', screenshots.screenshot_set_view),
    url(r'^screenshot_sets/(?P<set_id>[\w-]{11})/delete$', screenshots.screenshot_set_delete_view),
    url(r'^screenshot_sets/(?P<set_id>[\w-]{11})/duplicate$', screenshots.screenshot_set_duplicate_view),

    url(r'^screenshot_sets/(?P<set_id>[\w-]{11})/add_shot$', screenshots.screenshot_set_add_shot_view),
    url(r'^screenshot_sets/(?P<set_id>[\w-]{11})/create_bundle$', screenshots.screenshot_set_create_bundle_view),
    url(r'^screenshot_sets/bundle_status/(?P<bundle_id>[\w-]{11})$', screenshots.screenshot_set_bundle_status_view),

    url(r'^screenshot_sets/(?P<set_id>[\w-]{11})/download$', screenshots.screenshot_set_download_bundle_view),
    url(r'^screenshot_sets/(?P<set_id>[\w-]{11})/(?P<shot_id>[\w-]{11})$', screenshots.screenshot_shot_view),
    url(r'^screenshot_sets/(?P<set_id>[\w-]{11})/(?P<shot_id>[\w-]{11})/delete$', screenshots.screenshot_delete_shot_view),
    url(r'^screenshot_sets/(?P<set_id>[\w-]{11})/(?P<shot_id>[\w-]{11})/(?P<device_type>\w{1,32})$', screenshots.screenshot_create_override),
    url(r'^screenshot_sets/(?P<set_id>[\w-]{11})/(?P<shot_id>[\w-]{11})/(?P<device_type>\w{1,32})/delete$', screenshots.screenshot_delete_override),
    url(r'^screenshot_sets/archive_download/(?P<basename>[^/]+)$', screenshots.archive_download_view),


    # APP WEBSITES

    url(r'^websites$', websites.websites_view),
    url(r'^websites/example$', websites.get_example_website_view),
    url(r'^websites/check_domain_cname$', websites.check_domain_cname_view),
    url(r'^websites/domains/(?P<domain>[\w.-]+)$', websites.website_page_by_domain_view),
    url(r'^websites/domains/(?P<domain>[\w.-]+)/(?P<slug>[\w.-]+)$', websites.website_page_by_domain_view),
    url(r'^websites/track$', websites.track_website_view_view),
    url(r'^websites/(?P<website_id>[\w-]{11})$', websites.website_view),
    url(r'^websites/(?P<website_id>[\w-]{11})/delete$', websites.delete_website_view),
    url(r'^websites/(?P<website_id>[\w-]{11})/(?P<slug>[\w.-]+)$', websites.website_page_view),


    # SDK

    url(r'^sdk/tokens$', sdk.tokens_view),
    url(r'^sdk/tokens/create$', sdk.token_create_view),
    url(r'^sdk/tokens/get_or_create$', sdk.token_get_or_create_view),
    url(r'^sdk/tokens/identify/(?P<token>[\w-]+)$', sdk.token_identify_view),
    url(r'^sdk/tokens/(?P<token_id>[\w-]{11})$', sdk.token_view),
    url(r'^sdk/tokens/(?P<token_id>[\w-]{11})/expire$', sdk.token_expire_view),

    url(r'^sdk/apps$', sdk.apps_view),
    url(r'^sdk/apps/(?P<app_id_or_bundle_id>[\w.-]+)$', sdk.app_view),
    url(r'^sdk/apps/(?P<app_id_or_bundle_id>[\w.-]+)/itunes$', sdk.app_itunes_info_view),


    # TRACKING

    url(r'^track$', tracking.track_view),


    # RUNTIME CONFIG

    url(r'^config$', config.configs_view),
    url(r'^config/(?P<rule_id>[\w-]{11})$', config.config_rule_view),
    url(r'^config/(?P<rule_id>[\w-]{11})/delete$', config.config_rule_delete_view),

    url(r'^config/publish$', config.publish_rules_view),

    url(r'^config_interpolated$', config.config_interpolated_view),


    # USER INTELLIGENCE

    url(r'^user_intelligence/users$', user_intelligence.users_view),
    url(r'^user_intelligence/users/(?P<sdk_user_id>[\w-]{11})$', user_intelligence.user_view),
    url(r'^user_intelligence/visits$', user_intelligence.visits_view),


    # DEBUG STUFF

    # Called by pingdom to make sure we're healthy.
    url(r'^debug/health_check$', debug.health_check),
)
