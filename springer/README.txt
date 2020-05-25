Crawl multiple search result of Springer

to obtain article title and abstract for creating a corpus
runs in batch as there is a download limit
need to obtain personal api key and create a file named apikey.txt with the key in it

springer-api
- original attempt
- uses website's api
- doesn't work well, misses a lot of abstracts

springer-plus
- first run with api (fast)
- then manually find article missed by api

ggcleanup 
- self explanatory, messed up some small stuff and wrote another file for cleanup
- basically just tidy up and organising result
