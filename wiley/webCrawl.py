# from selenium import webdriver
from bs4 import BeautifulSoup
# import requests
from requests_html import HTMLSession
from crossref.restful import Works
from datetime import datetime
import pandas as pd
import re
import csv
import time

"""

webCrawler for wiley
save title, url, abstract of papers
run for around 7~8 batches because of download limit
- set last_idx and last_link in main
run first link separately with commented get_links

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
    # for link in soup1.select("a[class*=publication_title]"):
    #     doi = link['href']
    #     if doi.startswith("/doi/"):
    #         doi = doi[5:]
    #     url = "https://doi.org/" + str(doi)
    #     if url not in abstracts["URL"]:
    #         dois.append(doi)
    #         if debug:
    #             print("DOI: " + doi)
    # append_report(reportfile, "Number of papers in this page: " + str(len(dois)) + "\n")

    #   for first link
    for link in soup1.select("a[class*='title visitable']"):
        doi = link['href']
        url = str(doi)
        sub = re.compile("doi/(.*)")
        doi = sub.findall(doi)[0]
        if url not in abstracts["URL"]:
            dois.append(doi)
            if debug:
                print("DOI: " + doi)
    append_report(reportfile, "Number of papers in this page: " + str(len(dois)) + "\n")


def get_abstract_old(doi):
    """
    get text using browser
    :param doi: doi of article
    :return: abstract of article from webpage
    """
    # get paper's title and abstract from website
    link = "https://onlinelibrary.wiley.com/doi/" + doi
    if debug:
        print(link)

    try:
        session = HTMLSession()
        req = session.get(link)
        req.html.render(timeout=32)
        soup = BeautifulSoup(req.content, 'html.parser')
        session.close()
    except (ValueError, Exception) as e:
        # print(traceback.format_exc())
        print(e)
        try:
            session = HTMLSession()
            req = session.get(link)
            req.html.render()
            soup = BeautifulSoup(req.content, 'html.parser')
        except(ValueError, Exception) as err:
            print("Second try failed too: " + str(err))
            append_report(reportfile, "ERROR: Could not load " + link + "\n")
            return None

    abstract = soup.find('div', attrs={'class': ["article-section__content en main"]})
    # if debug:
    #     print(abstract)
    if abstract is None:
        abstract = soup.findAll('div', attrs={'class': 'article__body'})
        if abstract is None:
            append_report(reportfile, "Link " + link + " has nothing at all.\n")
            return None
        else:
            try:
                abstractText = abstract[0].p.extract()
                abstractText = abstractText.get_text(strip=True)
                append_report(reportfile, "Link " + link + " has no abstract.\n")
            except(ValueError, Exception):
                append_report(reportfile, "Link " + link + " has nothing at all.\n")
                return None
    else:
        abstractText = abstract.p.extract()
        abstractText = abstractText.get_text(strip=True)

    return abstractText


def get_abstracts(work, doi, jnum):
    n = 0
    for d in doi:
        #   get json response
        jresp = work.doi(d)
        jnum += 1

        #   make url with doi
        url = "https://doi.org/" + str(d)

        #   get title
        try:
            titles = jresp['title']
            title = ''
        except(ValueError, Exception):
            print(d + " is None type")
            continue
        if len(titles) == 0:
            try:
                title = titles[0]
            except(ValueError, Exception):
                title = ""
        else:
            for t in titles:
                title = title + t

        #   get abstract
        try:
            text = jresp['abstract']
            soup = BeautifulSoup(text, 'html.parser')
            text = soup.get_text(strip=True)
        except(ValueError, Exception):
            text = get_abstract_old(d)
            if text == "None" or text is None:
                print(str(d) + ": has no abstract")
                n += 1
        print(text)

        #   append to dataframe
        abstracts.loc[len(abstracts)] = [url, title, text]
        # temp = pd.DataFrame([url, title, text])
        append_abstract(abstractfile, [str(jnum), url, title, text])

    print("Total no abstract: " + str(n))
    append_report(reportfile, "Total no abstract: " + str(n) + ".\n\n")
    return jnum


#   change driver

if __name__ == '__main__':
    # variables initialization
    papers = []
    debug = True
    matchpdf = re.compile('.pdf')  # can use this to get pdf links!

    #   open files
    abstractfile = 'wiley_abstract.csv'
    reportfile = 'wiley_report.txt'
    header = ['jnum', 'title', 'url', 'abstract']
    with open(abstractfile, 'wt') as f:
        w = csv.writer(f)
        w.writerow(header)
    f.close()
    fr = open(reportfile, "wt")
    fr.write(str(datetime.now()) + " Start web crawling...\n\n")
    fr.close()
    abstracts = pd.DataFrame(columns=['URL', 'Title', 'Abstract'])

    # main webpages
    main_url = ["https://novel-coronavirus.onlinelibrary.wiley.com/novel-coronavirus-outbreak"]
    # main_url = ["https://onlinelibrary.wiley.com/action/doSearch?AfterYear=2017&AllField=coronavirus*+OR+%22sars-cov+2%22+OR+%22covid+19%22+OR+%222019-ncov%22&BeforeYear=2017&PubType=journal&sortBy=Earliest&startPage=2&pageSize=100"]
    # main_url = ["https://www.onlinelibrary.wiley.com/action/doSearch?=&=&=&=&=20200127-20200227&Ppub=&PubType=book&field1=Abstract&field2=AllField&field3=AllField&field4=AllField&field5=AllField&startPage=&text1=coronavirus*+OR+%22sars%22&text2=-%22sar+imaging%22&text3=-%22structure%E2%80%93activity+relationships%22&text4=-%22stock+appreciation+rights%22&text5=-%22space+age+remote+sensing%22&pageSize=100"]
    # for y in reversed(range(1883, 2021)):
    # for y in reversed(range(1883, 2019)):
    #     long_url = "https://onlinelibrary.wiley.com/action/doSearch?AllField=coronavirus*+OR+%22sars-cov+2%22+OR+%22covid+19%22+OR+%222019-ncov%22&PubType=journal&sortBy=Earliest&startPage=&pageSize=100&AfterYear=" + str(
    #         y) + "&BeforeYear=" + str(y)
    #     main_url.append(long_url)

    page = 0
    j = 0
    last_idx = 0    # set here for batch runs
    last_link = ""
    for idx, main in enumerate(main_url):
        if idx < last_idx:
            continue
        if idx == last_idx:
            if last_link != "":
                main = last_link
        i = 1
        print("Visiting: " + main)
        append_report(reportfile, "LINK " + str(idx+1) + " : " + main + "\n\n")
        while True:
            page += 1
            # #   code always mysteriously stop at the 14th page it visits
            # if page % 14 == 0:
            #     print("Reached page " + str(page))
            #     append_report(reportfile, "\n" + str(datetime.now()) + " Reached page " + str(page) + "\n\n")
            #     # print("Sleeping for 30 mins...")
            #     # append_report(reportfile, "\n" + str(datetime.now()) + " Sleeping...\n\n")
            #     # time.sleep(1800)     # let program sleep for 30 mins
            try:
                sess = HTMLSession()
                r = sess.get(main)
                r.html.render(timeout=60)
                time.sleep(0.5)
                soup0 = BeautifulSoup(r.content, 'html.parser')
                sess.close()
            except(ValueError, Exception):
                try:
                    sess = HTMLSession()
                    r = sess.get(main)
                    r.html.render(timeout=60)
                    time.sleep(0.5)
                    soup0 = BeautifulSoup(r.content, 'html.parser')
                    sess.close()
                except(ValueError, Exception) as e:
                    print("Second try failed too: " + str(e))
                    append_report(reportfile, "ERROR: Could not load " + main + "\n\n")

            links = []
            get_links(soup0, links)
            works = Works()
            j = get_abstracts(works, links, j)

            # go to next page
            i += 1
            nextpage = soup0.select("a[title='Next page']")
            if i != 1 and len(links) < 100:
                if debug:
                    print("Last page has " + str(len(links)) + "result")
                    append_report(reportfile, "Last page. Number of links: " + str(len(links)) + "\n\n")
                    # time.sleep(300)
                break
            elif len(nextpage) == 1:
                main = nextpage[0]['href']
                if main != "":
                    print("********************** " + str(
                        i) + " GOING TO NEXT PAGE: " + main + " **********************")
                    append_report(reportfile, "Going to page " + str(i) + "\n")
                    append_report(reportfile, main + "\n")
                    if j > 850:
                        last_link = main
                        break
            else:
                if debug:
                    print("nextpage length = " + str(len(nextpage)))
                    append_report(reportfile, "No link to page " + str(i) + "\n\n")
                break

        if j > 850:
            if last_link == "":
                print("Reached j=" + str(j) + ", next page idx = " + str(idx + 1))
                append_report(reportfile, str(datetime.now()) + " Reached j=" + str(j) + ", next page idx = " + str(idx + 1) + "\n\n")
            else:
                print("Reached j=" + str(j) + ", this page idx = " + str(idx))
                append_report(reportfile, str(datetime.now()) + " Reached j=" + str(j) + ", this page idx = " + str(
                    idx) + "\n\n")
            break

    abstracts.to_csv(r'abstracts-wiley.txt', sep='\t', mode='w')

    append_report(reportfile, "End Crawling!\n")
    
    ###
    #
    #   after batch running use code below to join all the abstracts
    #
    ###
    
#    a = pd.read_csv(r'/Users/vickybang/PycharmProjects/webCrawler/venv/wiley-batch/batch0/abstracts-wiley0.txt', sep='\t', index_col=False)
#    for i in range(batches):
#        a = a.append(pd.read_csv(r'/Users/vickybang/PycharmProjects/webCrawler/venv/wiley-batch/batch'+str(i+1)+'/abstracts-wiley'+str(i+1)+'.txt', sep='\t', index_col=False), ignore_index=True)
#    a = a.drop(['Unnamed: 0'], axis=1)
#    a.to_csv(r'abstract-wiley.txt', sep='\t', mode='w')
