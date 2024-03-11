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

### Crawler:
1. Crawler service that crawles new data (i.e blogs), every X seconds, pretty much the same as shows in this requests code.
2. Spider (scrapy) that indexes new data (i.e pages) on indexed links (i.e blogs) every X seconds

### Index:
1. solr/typesense index, holds docs (i.e pages) that has been optimized with keywords analasis and weights.
2. recieves the search query, passes it through the pipelines of analasis (dropping block-words, keyword extraction) and compares against index
 
