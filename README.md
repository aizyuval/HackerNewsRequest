# Hacker News Request Service

Limited by the HN API native item-like sorting, to fetch all stories one needs to fetch 
each and everyone of the items and determine weather it is valid story or not.

It fetches backwords, from the MAXITEM currently available on HN, to the bottom. It logs everything all the way down,
and also logs where was the last time it was interrupted.

It uses postgresql for the database, which is set up locally (though can be remote)
Log and .env file are to be setup locally.

The only purpose of this scraper is to gather a bulk of stories/show_hn out of hn. 


# Hacker News Blog Search

The latter is going to set a list of links to be parsed for determining blog statuses. Then, on top of these blogs as index, there will be:

crawler (native python requests / HN api)
db (postgresql)
index + search (solr/typesense)

Main challange is to determine blog position by link to the site.
