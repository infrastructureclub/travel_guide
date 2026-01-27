#!/usr/bin/env python3
import json
from datetime import datetime, timezone

from dateutil import parser
from feedgen.feed import FeedGenerator

with open('./data/map.json') as f:
    data = json.load(f)

places_list = sorted(data["places"].values(), key=lambda x: x["created"], reverse=True)

fg = FeedGenerator()
fg.id('https://infrastructureclub.org/travel_guide/')
fg.title('Infrastructure Club Travel Guide - New Places')
fg.author( {'name':'Infrastructure Club'} )
fg.subtitle('Latest places added to the travel guide')
fg.link( href='https://github.com/infrastructureclub/travel_guide', rel='alternate' )
fg.language('en')

latest_date = None
for place in places_list[:50]:
    date = parser.parse(place["created"])
    date = date.replace(tzinfo=timezone.utc)

    if not latest_date or date > latest_date:
        latest_date = date

    fe = fg.add_entry()
    fe.id(place["id"])
    fe.published(published=date)
    fe.updated(updated=date)
    fe.title(f'{place["name"]} added to the travel guide')
    fe.link(href=f'https://infrastructureclub.org/travel_guide/#{place["id"]}')

fg.updated(latest_date)
fg.rss_file('data/rss.xml', pretty=True)
