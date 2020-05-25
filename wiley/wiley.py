#from selenium import webdriver
from bs4 import BeautifulSoup
# import requests
from requests_html import HTMLSession
from crossref.restful import Works
import pandas as pd
import re
import csv
import time

"""

webCrawler for wiley
save title, url, abstract of papers

"""


def append_abstract(abstractFileName, paper):
    #   append to abstract file
    #   call after file is opened
    with open(abstractFileName, 'at') as f1:
        w1 = csv.writer(f1)
        w1.writerow(paper)


def append_report(reportFileName, string):
    #   append to report file
    f2 = open(reportFileName, 'at')
    f2.write(string)


def get_links(soup1, dois):
    for link in soup1.select("a[class*=publication_title]"):
        doi = link['href']
        if doi.startswith("/doi/"):
            doi = doi[5:]
        dois.append(doi)
        if debug:
            print("DOI: " + doi)
    append_report(reportfile, "Number of papers in this page: " + str(len(links)) + "\n")


def get_abstracts(work, doi):

    # get paper's title and abstract from website
    # for idx, link in enumerate(links):
    #     if debug:
    #         print(link)

        # try:
        #     session = HTMLSession()
        #     req = session.get(link)
        #     req.html.render()
        #     soup = BeautifulSoup(req.content, 'html.parser')
        #     session.close()
        # except (ValueError, Exception) as e:
        #     # print(traceback.format_exc())
        #     print(e)
        #     session = HTMLSession()
        #     req = session.get(link)
        #     req.html.render()
        #     soup = BeautifulSoup(req.content, 'html.parser')
        #
        # title = soup.find('h1', attrs={'class': ["citation__title"]}).extract()
        # title = title.get_text(strip=True)
        #
        # if debug:
        #     print(title)
        # abstract = soup.find('div', attrs={'class': ["article-section__content en main"]})
        # # if debug:
        # #     print(abstract)
        # if abstract is None:
        #     abstract = soup.findAll('div', attrs={'class': 'article__body'})
        #     abstractText = abstract[0].p.extract()
        #     abstractText = abstractText.get_text(strip=True)
        #     append_report(reportfile, "Link " + str(idx) + " has no abstract.\n")
        # else:
        #     abstractText = abstract.p.extract()
        #     abstractText = abstractText.get_text(strip=True)
    n = 0
    for d in doi:
        #   get json response
        jresp = work.doi(d)

        #   make url with doi
        url = "https://doi.org/" + str(d)

        #   get title
        titles = jresp['title']
        title = ''
        if len(titles) == 0:
            title = titles[0]
        else:
            for t in titles:
                title = title + t

        #   get abstract
        try:
            text = jresp['abstract']
        except(ValueError, Exception):
            print(str(d) + ": has no abstract")
            n += 1
            continue
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text(strip=True)
        print(text)

        #   append to dataframe
        abstracts.loc[len(abstracts)] = [url, title, text]
        # temp = pd.DataFrame([url, title, text])

        append_abstract(abstractfile, [url, title, text])
    print("No abstract: " + str(n))


#   change driver

if __name__ == '__main__':
    # variables initialization
    papers = []
    debug = True
    matchpdf = re.compile('.pdf')  # can use this to get pdf links!

    #   open files
    abstractfile = 'wiley_abstract.csv'
    reportfile = 'wiley_report.txt'
    header = ['title', 'url', 'abstract']
    with open(abstractfile, 'wt') as f:
        w = csv.writer(f)
        w.writerow(header)
    f.close()
    fr = open(reportfile, "wt")
    fr.write("Start web crawling...\n\n")
    fr.close()
    abstracts = pd.DataFrame(columns=['URL', 'Title', 'Abstract'])

    # main webpages
    main_url = []
    # main_url = ["https://novel-coronavirus.onlinelibrary.wiley.com/novel-coronavirus-outbreak",
    #             "https://www.onlinelibrary.wiley.com/action/doSearch?=&=&=&=&=20200127-20200227&Ppub=&PubType=book&field1=Abstract&field2=AllField&field3=AllField&field4=AllField&field5=AllField&startPage=&text1=coronavirus*+OR+%22sars%22&text2=-%22sar+imaging%22&text3=-%22structure%E2%80%93activity+relationships%22&text4=-%22stock+appreciation+rights%22&text5=-%22space+age+remote+sensing%22"]
    for y in range(1883, 2020):
        long_url = "https://onlinelibrary.wiley.com/action/doSearch?AllField=coronavirus*+OR+%22sars-cov+2%22+OR+%22covid+19%22+OR+%222019-ncov%22&PubType=journal&sortBy=Earliest&startPage=&pageSize=100&AfterYear=" + str(y) + "&BeforeYear=" + str(y)
        main_url.append(long_url)

    for main in main_url:
        i = 1
        print("Visiting: " + main)
        append_report(reportfile, "LINK 1 : " + main + "\n\n")
        while True:
            sess = HTMLSession()
            r = sess.get(main)
            r.html.render()
            soup0 = BeautifulSoup(r.content, 'html.parser')
            sess.close()

            links = []
            get_links(soup0, links)
            works = Works()
            get_abstracts(works, links)

            # go to next page
            i += 1
            nextpage = soup0.select("a[title='Next page']")
            if i != 1 and len(links) < 100:
                if debug:
                    print("This page has less than" + str(len(links)) + "result")
                    append_report(reportfile, "Last page. Number of links: " + str(len(links)) + "\n")
                break
            if len(nextpage) == 1:
                link0 = nextpage[0]['href']
                if link0 == "":
                    print("********************** " + str(i) + " GOING TO NEXT PAGE: " + link0 + " **********************")
                    append_report(reportfile, "Going to page " + str(i) + "\n")
                    append_report(reportfile, link0 + "\n")
            else:
                if debug:
                    print("nextpage length = " + str(len(nextpage)))
                    append_report(reportfile, "No link to page " + str(i) + "\n")
                break

    append_report(reportfile, "End Crawling!\n")
    abstracts.to_csv(r'abstracts-wiley.txt', sep='\t', mode='w')
