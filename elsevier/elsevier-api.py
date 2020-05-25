# -*- coding: utf-8 -*-

####
# Prerequisites:
# - Get an API key from dev.elsevier.com, and store as a single string, without
#   line break, in apikey.txt in same folder as this script

import requests
import pandas as pd
import json
from datetime import date
from elsapy.elsclient import ElsClient
from elsapy.elsprofile import ElsAuthor, ElsAffil
from elsapy.elsdoc import FullDoc, AbsDoc
from elsapy.elssearch import ElsSearch
import json
import traceback
import time


def append_report(reportFileName, string):
    #   append to report file
    f2 = open(reportFileName, 'at')
    f2.write(string)
    f2.close()


## Load configuration
con_file = open("config.json")
config = json.load(con_file)
con_file.close()

## Initialize client
client = ElsClient(config['apikey'])
client.inst_token = config['insttoken']

# Get APIkey
with open('apikey.txt') as f:
    apikey = f.read()

# Set request headers
headers = {
        'X-ELS-APIkey':  str(apikey).rstrip('\n'),
        'Accept': 'application/json'
        }

#   set year to get smaller search result since elsevier limit start=6000
years = ["1970-2000", "2001-2005", "2006-2010", "2011-2015", "2016-2018", "2019-2020"]
# years = ["2000", "2001"]    # test
url_front = 'https://api.elsevier.com/content/search/sciencedirect?start='
url_start = str(0)
url_back = '&query="COVID-19"%20OR%20Coronavirus%20OR%20"Corona%20virus"%20OR%20"2019-nCoV"%20OR%20"SARS-CoV"%20OR%20"MERS-CoV"'
pii_total = []
ntotal = 0
err = 0

#   open file
abstract = pd.DataFrame(columns=["URL", "Title", "Abstract"])
with open('abstracts1.txt', 'w') as f:
    abstract.to_csv(f, sep='\t')
f.close()
reportName = "elsevier-api-report.txt"
fr = open(reportName, 'wt')
fr.write("Start web crawling...\n\n\n")
fr.close()

for year in years:
    append_report(reportName, "Searching for year " + year + "...\n")
    url_date = '&count=100&date=' + year
    base_url = url_front + url_start + url_date + url_back
    r = requests.get(base_url, headers=headers)
    resp = json.loads(r.content)
    # print(resp)
    total = resp['search-results']['opensearch:totalResults']
    totalpages = (int(total)//100)+1
    print("Total entries: " + total)
    print("Total pages: " + str(totalpages))

    #   loop through all 232 pages (100 articles each page)
    # ktest = [14, 15]
    # for k in ktest:
    for k in range(totalpages):
        print("**************************** Page " + str(k+1) + " ****************************")
        append_report(reportName, "Going to page " + str(k+1) + "...\n")
        # Define elements of request URL
        url = url_front + str(k*100) + url_date + url_back
        try:
            time.sleep(0.5)     # create delays between requests to prevent error
            r = requests.get(url, headers=headers)
            time.sleep(0.5)
            resp = json.loads(r.text)
        except(ValueError, Exception) as e:
            print(traceback.format_exc())
            print(e)
            append_report(reportName, "Fail loading json page " + str(k) + "\n")
            append_report(reportName, "Error message: " + str(e) + "\n")
            continue


        #   get pii of all 100 links
        links = []
        pii = []
        papers = resp['search-results']['entry']
        i = 0
        for paper in papers:
            link = papers[i]['link'][0]['@href']
            idx = link.find('pii/')
            pii.append(link[idx+4:])
            i += 1

        #   remove duplicates
        for pii_this in pii:
            if pii_this in pii_total:
                pii.remove(pii_this)
        pii_total.extend(pii)

        #   get url, title, and abstract of all 100 articles
        n = 0
        j = 1
        for p in pii:
            pii_doc = FullDoc(sd_pii=p)
            try:
                if pii_doc.read(client):
                    #   get title
                    title = pii_doc.title
                    title.strip()
                    title.replace('\n', ' ')
                    #   get abstract
                    text = pii_doc.data["coredata"]["dc:description"]
                    if text is not None:
                        text = text.strip()
                        if text.startswith(('ABSTRACT', 'Abstract', 'Summary')):
                            text = text[8:]
                            text = text.strip()
                        # remove extra whitespace
                        text.replace("\n", "")
                        text = " ".join(text.split())
                    else:
                        n += 1
                    #   get url
                    url = pii_doc.data["coredata"]["link"][1]["@href"]
                    #   save data
                    abs = pd.DataFrame([url, title, text])
                    abstract.loc[len(abstract)] = [url, title, text]
                    abs.to_csv(r'abstracts1.txt', sep='\t', mode='a', header=False, index=False)
                    print(str(j) + ") pii_doc.title: ", title)
                    print("pii_doc.description: ", text)
                    print("pii_doc.url: ", url)
                    pii_doc.write()
                    j += 1
                else:
                    print("Read document failed.")
            except(ValueError, Exception) as e:
                print(str(j) + ") " + str(e))
                append_report(reportName, "Fail reading document " + str(j) + ", pii: " + str(p) + "\n")
                append_report(reportName, "Error message: " + str(e) + "\n")
                err += 1
                j += 1
        append_report(reportName, "Total " + str(n) + " null abstract \n\n")
        ntotal += n


#   output results
abstract.to_csv(r'abstracts.txt', sep='\t', mode='w')
result = "Finish crawling! \n" + "Total " + str(ntotal) + "/" + str(len(pii_total)) + " null abstracts ("
result2 = str(ntotal*100.0/len(pii_total)) + "%)\nTotal " + str(err) + " failed document read\n"
result3 = "Valid documents: " + str(len(pii_total)-ntotal-err) + "\n"
append_report(reportName, result + result2 + result3)


####################################################
## ScienceDirect (full-text) document example using PII
# pii_doc = FullDoc(sd_pii='S0891552019300601')
# if pii_doc.read(client):
#     print("pii_doc.title: ", pii_doc.title)
#     pii_doc.write()
# else:
#     print("Read document failed.")

