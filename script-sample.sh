#!/usr/bin/env bash

DOMAIN=example.com
SITE_ROOT=http://$DOMAIN

scrapy crawl site \
    -s DOMAIN=$DOMAIN \
    -s START_URLS=$SITE_ROOT,$SITE_ROOT/robots.txt,$SITE_ROOT/sitemap.xml \
    -s DIR_ROOT=/var/www/static/$SITE_ROOT \
    -s USER_AGENT='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/51.0.2704.79 Chrome/51.0.2704.79 Safari/537.36'
    # USER_AGENT='Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.23 Mobile Safari/537.36',
