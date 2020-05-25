import requests
import json
import pandas as pd
import time
from datetime import datetime
from bs4 import BeautifulSoup
from requests_html import HTMLSession

#   pip install websockets==6.0 --force-reinstall

"""

webCrawler for Springer
use browsers as backup
get title, url, abstract of articles
can get pdf url too (abs_pdf)

"""


def append_report(reportFileName, string):
    #   append to report file
    f2 = open(reportFileName, 'at')
    f2.write(string)


def get_links(soup1, dois):
    dois2 =[]
    urls = []
    links = soup1.select("a[class='title']")
    for link in links:
        doi = link['href']
        if doi.startswith('/article/') or doi.startswith('/chapter/'):
            doi = doi[9:]
        elif doi.startswith('/referenceworkentry/'):
            doi = doi[20:]
        elif doi.startswith('/protocol/'):
            doi = doi[10:]
        elif doi.startswith('/book/'):
            doi = doi[6:]
        if doi not in dois:
            dois2.append(doi)
            print("DOI: " + doi)
            urls.append(link['href'])
        else:
            print(doi + " is in dois")
    append_report(reportfile, "Number of papers in this page: " + str(len(dois2)) + "/" + str(len(links)) + "\n")

    return dois2, urls


def get_abstract_old(link):
    """
    :param link: url of article
    :return: title, url_pdf, abstract
    """
    s1 = HTMLSession()
    r1 = s1.get(link)
    r1.html.render(timeout=120)
    time.sleep(0.5)
    soup1 = BeautifulSoup(r1.content, 'html.parser')
    s1.close()

    title1 = soup1.select("h1[class*='article-title']")
    if soup1.find('h2', text='Abstract') is not None:
        text = soup1.find('h2', text='Abstract').next_sibling
        text = text.get_text(" ")
    elif soup1.find('h2', text='Introduction') is not None:
        text = soup1.find('h2', text='Introduction').next_sibling
        text = text.get_text(" ")
    else:
        text = ''
    pdf = soup1.select('a[href*=".pdf"]')
    if len(pdf) != 0:
        pdf = pdf[0]['href']
    else:
        pdf = ''

    return title1, pdf, text


def get_abstracts(dois2, urls):
    """
    update abstracts dataframe
    :param dois2: list of dois to visit
    :param urls: list of links to visit
    :return:
    """
    n0 = 0
    for idx, d in enumerate(dois2):
        link = "http://api.springernature.com/meta/v2/json?q=doi:" + d + "&api_key=" + apikey
        # url_article = 'https://doi.org/' + d
        print(urls[idx])
        link1 = "https://link.springer.com" + urls[idx]

        try:
            r2 = requests.get(link)
            resp2 = json.loads(r2.content)
            title1 = resp2['records']['title']
            abstract1 = resp2['records']['abstract']
            #   pdf link
            pdf = ''
            for j in range(len(resp2['records']['url'])):
                if resp2['records']['url'][j]['format'] == 'pdf':
                    pdf = resp2['records']['url'][j]['value']
        except(ValueError, BaseException) as e:
            print(e)
            try:
                title1, pdf, abstract1 = get_abstract_old(link1)
            except(ValueError, Exception) as e:
                print(e)
                title1 = ''
                pdf = ''
                abstract1 = ''

        if abstract1 == '' or abstract1 is None:
            n0 += 1
            print(link1 + ": has no abstract")
            append_report(reportfile, link1 + " has no abstract\n")

        print(link1)
        print(abstract1)

        #   append to dataframe
        abstracts.loc[len(abstracts)] = [link1, title1, abstract1]
        abs_pdf.loc[len(abs_pdf)] = [link1, pdf, title1, abstract1]

        temp = pd.DataFrame(columns=['URL', 'PDF', 'Title', 'Abstract'])
        temp.loc[0] = [link1, pdf, title1, abstract1]
        temp.to_csv(r'abscheck.txt', sep='\t', mode='a', header=False)

    append_report(reportfile, "\n" + str(n0) + "/" + str(len(dois2)) + " no abstract\n\n")


def get_prev_batch(filename):
    """
    read in [0, URL, PDF, TITLE, ABSTRACT] to abstracts
    :param filename: file path to file containing previous info
    :return: dois, abstracts
    """

    #   read previous batch
    abstracts0 = pd.read_csv(filename, sep='\t', index_col=False)
    abstracts0 = abstracts0.drop(['Unnamed: 0'], axis=1)
    print("Previous total abstracts: " + str(len(abstracts0)))

    #   get prev dois
    dois0 = []
    n0 = 0
    for k in range(len(abstracts0)):
        link = abstracts0['URL'][k]
        if link.startswith('https://doi.org/'):
            dois0.append(link[16:])
        elif link.startswith('https://link.springer.com'):
            link = link[25:]
            if link.startswith('/article/') or link.startswith('/chapter/'):
                link = link[9:]
            elif link.startswith('/referenceworkentry/'):
                link = link[20:]
            elif link.startswith('/protocol/'):
                link = link[10:]
            elif link.startswith('/book/'):
                link = link[6:]
            else:
                n0 += 1
            dois0.append(link)
        else:
            n0 += 1
    if n0 > 0:
        print("THERE IS " + str(n0) + " MISSED DOI")
        append_report(reportfile, "\n***!!! THERE IS " + str(n0) + " MISSED DOI !!!***\n")
    else:
        append_report(reportfile, "Get previous batch SUCCESS\n")

    print("Number of dois: " + str(len(dois0)))

    return dois0, abstracts0


if __name__ == '__main__':
    #   initialize dataframe
    abstracts = pd.DataFrame(columns=["URL", "Title", "Abstract"])
    abs_pdf = pd.DataFrame(columns=['URL', 'PDF', 'Title', 'Abstract'])

    #   open report file
    reportfile = 'springer_report.txt'
    fr = open(reportfile, "wt")
    fr.write(str(datetime.now()) + " Start web crawling...\n\n")
    fr.close()
    with open('abscheck.txt', 'w') as f:
        abs_pdf.to_csv(f, sep='\t')
    f.close()

    #   Get APIkey
    with open('apikey.txt') as f:
        apikey = f.read()
    f.close()

    # ##
    # #
    # #       get abstracts with api
    # #       fast but limited number of results
    # #       comment out when running second batch
    # #
    # ##
    #
    # #   construct url = 1 + year + 2 + start + 3 + apikey
    # url_1 = "http://api.springernature.com/meta/v2/json?q=(%22coronavirus%22%20AND%20year:%22"
    # url_2 = "%22)&s="
    # url_3 = "&p=100&api_key="
    #
    # dois = []
    # #   year loop
    # # for year in reversed(range(2020, 2021)):
    # for year in reversed(range(1838, 2021)):
    #     url = url_1 + str(year) + url_2 + "1" + url_3 + apikey
    #     print("****************************** YEAR : " + str(year) + " ******************************")
    #     print(url)
    #     append_report(reportfile, "************************* YEAR : " + str(year) + " *************************\n")
    #     append_report(reportfile, url + "\n\n")
    #
    #     #   get info
    #     r = requests.get(url)
    #     resp = json.loads(r.content)
    #     total = int(resp['result'][0]['total'])  # total result from this year
    #     print("Total of article: " + str(total))
    #     append_report(reportfile, "Total of article: " + str(total))
    #
    #     n = 0  # number of null abstract
    #
    #     #   page loop
    #     for s in range(total // 100 + 1):
    #         url = url_1 + str(year) + url_2 + str(s * 100 + 1) + url_3 + apikey
    #         print("Visiting page: " + str(s + 1) + "...")
    #         append_report(reportfile, "Page: " + str(s + 1) + "\n")
    #
    #         r = requests.get(url)
    #         resp = json.loads(r.content)
    #
    #         for i in range(len(resp['records'])):
    #
    #             #   get title, url, abstract
    #             title = resp['records'][i]['title']
    #             doi = resp['records'][i]['doi']
    #             dois.append(doi)
    #             url_article = 'https://doi.org/' + doi
    #             abstract = resp['records'][i]['abstract']
    #             if abstract == '':
    #                 n += 1
    #                 print(url_article + ": has no abstract")
    #                 append_report(reportfile, url_article + " has no abstract\n")
    #             #   pdf link
    #             url_pdf = ''
    #             for j in range(len(resp['records'][i]['url'])):
    #                 if resp['records'][i]['url'][j]['format'] == 'pdf':
    #                     url_pdf = resp['records'][i]['url'][j]['value']
    #
    #             print(url_article)
    #             print(abstract)
    #
    #             #   append to dataframe
    #             abstracts.loc[len(abstracts)] = [url_article, title, abstract]
    #             abs_pdf.loc[len(abs_pdf)] = [url_article, url_pdf, title, abstract]
    #             temp = pd.DataFrame(columns=['URL', 'PDF', 'Title', 'Abstract'])
    #             temp.loc[0] = [url_article, url_pdf, title, abstract]
    #             temp.to_csv(r'abscheck.txt', sep='\t', mode='a', header=False)
    #
    #     append_report(reportfile, "\n" + str(n) + "/" + str(total) + " no abstract\n\n")

    ##
    #
    #       manually using browser
    #       i = start page
    #       if second batch, uncomment get_prev_batch, change i and main_url
    ##
    i = 342

    dois, abs_pdf = get_prev_batch('batch1/abscheck0.txt')
    abstracts = abs_pdf.drop(['PDF'], axis=1)

    # main_url = "https://link.springer.com/search?facet-language=%22En%22&package=coronavirus"
    main_url = "https://link.springer.com/search/page/342?facet-language=%22En%22&package=coronavirus"
    while True:
        sess = HTMLSession()
        r = sess.get(main_url)
        r.html.render()
        time.sleep(0.5)
        soup = BeautifulSoup(r.content, 'html.parser')
        sess.close()

        #   get number of pages
        pages = soup.select("span[class='number-of-pages']")
        pages = int(pages[0].get_text())

        dois2 = []
        dois2, urls = get_links(soup, dois)
        get_abstracts(dois2, urls)

        # go to next page
        i += 1
        if i <= pages:
            main_url = "https://link.springer.com/search/page/" + str(i) + "?facet-language=%22En%22&package=coronavirus"
            print("********************** " + str(
                i) + " GOING TO NEXT PAGE: " + main_url + " **********************")
            append_report(reportfile, "Going to page " + str(i) + "\n")
            append_report(reportfile, main_url + "\n")
        else:
            print("Finished last page")
            append_report(reportfile, "Finished last page " + str(i) + "\n\n")
            break

        # nextpage = soup.select("a[class='next']")
        # if i != 1 and len(links) < 100:
        #     if debug:
        #         print("Last page has " + str(len(links)) + "result")
        #         append_report(reportfile, "Last page. Number of links: " + str(len(links)) + "\n\n")
        #         # time.sleep(300)
        #     break
        # if len(nextpage) == 2:
        #     main = nextpage[0]['href']
        #     if main != "":
        #         main_url = "https://link.springer.com" + main
        #         print("********************** " + str(
        #             i) + " GOING TO NEXT PAGE: " + main + " **********************")
        #         append_report(reportfile, "Going to page " + str(i) + "\n")
        #         append_report(reportfile, main + "\n")
        # else:
        #     print("nextpage length = " + str(len(nextpage)))
        #     append_report(reportfile, "No link to page " + str(i) + "\n\n")
        #     break


    #   output result
    abstracts.to_csv(r'abstracts-springer.txt', sep='\t', mode='w')
    append_report(reportfile, "End Crawling!\n")


