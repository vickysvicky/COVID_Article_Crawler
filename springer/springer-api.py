import requests
import json
import pandas as pd
from datetime import datetime

# from bs4 import BeautifulSoup

"""

webCrawler for Springer
get title, url, abstract of articles
can get pdf url too (abs_pdf)

"""


def append_report(reportFileName, string):
    #   append to report file
    f2 = open(reportFileName, 'at')
    f2.write(string)


if __name__ == '__main__':
    #   open report file
    reportfile = 'springer_report.txt'
    fr = open(reportfile, "wt")
    fr.write(str(datetime.now()) + " Start web crawling...\n\n")
    fr.close()

    #   initialize dataframe
    abstracts = pd.DataFrame(columns=["URL", "Title", "Abstract"])
    abs_pdf = pd.DataFrame(columns=['URL', 'PDF', 'Title', 'Abstract'])

    #   Get APIkey
    with open('apikey.txt') as f:
        apikey = f.read()
    f.close()

    #   construct url = 1 + year + 2 + start + 3 + apikey
    url_1 = "http://api.springernature.com/meta/v2/json?q=(%22coronavirus%22%20AND%20year:%22"
    url_2 = "%22)&s="
    url_3 = "&p=100&api_key="

    #   year loop
    for year in reversed(range(1838, 2021)):
        url = url_1 + str(year) + url_2 + "1" + url_3 + apikey
        print("****************************** YEAR : " + str(year) + " ******************************")
        print(url)
        append_report(reportfile, "************************* YEAR : " + str(year) + " *************************\n")
        append_report(reportfile, url + "\n\n")

        #   get info
        r = requests.get(url)
        resp = json.loads(r.content)
        total = int(resp['result'][0]['total'])  # total result from this year
        print("Total of article: " + str(total))
        append_report(reportfile, "Total of article: " + str(total))

        n = 0  # number of null abstract

        #   page loop
        for s in range(total // 100 + 1):
            url = url_1 + str(year) + url_2 + str(s * 100 + 1) + url_3 + apikey
            print("Visiting page: " + str(s + 1) + "...")
            append_report(reportfile, "Page: " + str(s + 1) + "\n")

            r = requests.get(url)
            resp = json.loads(r.content)

            for i in range(len(resp['records'])):

                #   get title, url, abstract
                title = resp['records'][i]['title']
                url_article = 'https://doi.org/' + resp['records'][i]['doi']
                abstract = resp['records'][i]['abstract']
                if abstract == '':
                    n += 1
                    print(url_article + ": has no abstract")
                    append_report(reportfile, url_article + " has no abstract\n")
                    continue
                #   pdf link
                for j in range(len(resp['records'][i]['url'])):
                    url_pdf = ''
                    if resp['records'][i]['url'][j]['format'] == 'pdf':
                        url_pdf = resp['records'][i]['url'][j]['value']

                print(url_article)
                print(abstract)

                #   append to dataframe
                abstracts.loc[len(abstracts)] = [url, title, abstract]
                abs_pdf.loc[len(abs_pdf)] = [url, url_pdf, title, abstract]

        append_report(reportfile, "\n" + str(n) + "/" + str(total) + " no abstract\n\n")

    #   output result
    abstracts.to_csv(r'abstracts-springer.txt', sep='\t', mode='w')
    append_report(reportfile, "End Crawling!\n")


