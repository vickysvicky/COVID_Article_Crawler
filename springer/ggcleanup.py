# from springer-plus import *

import pandas as pd
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import time

abs = pd.read_csv(r'abstracts-springer-fixed0.txt', sep='\t')
abs = abs.drop(['Unnamed: 0', 'Unnamed: 0.1'], axis=1)

#   get index of incorrect title
fail = []
nan = []
strip = []
blank = []
for i in range(len(abs)):
    title = abs['Title'][i]
    if str(title) == 'nan':
        nan.append(i)
    elif title.startswith('[<h1 class'):
        strip.append(i)
    elif title == '[]':
        blank.append(i)


#   strip previous title with tag
for i in strip:
    soup = BeautifulSoup(abs['Title'][i], 'html.parser')
    title = soup.get_text(" ")
    title = title[1:-1]
    title = ' '.join(title.split())
    abs['Title'][i] = title

#   get correct title for nan
for i in nan:
    link = abs['URL'][i]
    s1 = HTMLSession()
    r1 = s1.get(link)
    r1.html.render(timeout=120)
    soup1 = BeautifulSoup(r1.content, 'html.parser')
    s1.close()
    title = soup1.select("h1[class*='article-title']")
    if len(title) == 1:
        title = title[0].get_text(" ")
        title = ' '.join(title.split())
        abs['Title'][i] = title
    else:
        fail.append(i)
        print("FAILED: " + abs['URL'][i])

#   get title for missed
for idx, i in enumerate(blank):
    print(str(idx+1) + "/" + str(len(blank)) + " Reading " + str(i) + " article")
    link = abs['URL'][i]
    s1 = HTMLSession()
    r1 = s1.get(link)
    r1.html.render(timeout=120)
    time.sleep(0.5)
    soup1 = BeautifulSoup(r1.content, 'html.parser')
    s1.close()
    title = soup1.select("h1[class*='ChapterTitle']")
    title2 = soup1.select("div[class*='page-title']")
    if len(title) == 1:
        title = title[0].get_text(" ")
        title = ' '.join(title.split())
        abs['Title'][i] = title
    elif len(title2) > 0:
        title2 = title2[0].get_text(" ")
        title2 = ' '.join(title2.split())
        abs['Title'][i] = title2
    else:
        fail.append(i)
        print("FAILED: " + abs['URL'][i])


#   output fixed dataframe
abs.to_csv(r'abstracts-springer-fixed.txt', sep='\t', mode='w')
print("Done fixing. Proceeding to remove non english article.")


###################################################
#         TO REMOVE NON-ENGLISH ARTICLE           #
###################################################
#   get dois of all article
dois = []
n0 = 0
for k in range(len(abs)):
    link = abs['URL'][k]
    if link.startswith('https://doi.org/'):
        dois.append(link[16:])
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
        dois.append(link)
    else:
        n0 += 1
if n0 > 0:
    print("THERE IS " + str(n0) + " MISSED DOI")
else:
    print("Get previous batch SUCCESS")
print("Number of dois: " + str(len(dois)))

#   get dois of english article
i = 1
main_url = "https://link.springer.com/search?facet-language=%22En%22&package=coronavirus"
doisEng = []
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

    links = soup.select("a[class='title']")
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
        doisEng.append(doi)

    # go to next page
    i += 1
    if i <= pages:
        main_url = "https://link.springer.com/search/page/" + str(i) + "?facet-language=%22En%22&package=coronavirus"
        print("********************** " + str(
            i) + " GOING TO NEXT PAGE: " + main_url + " **********************")
    else:
        print("Finished last page")
        break

#   find index of non english article
print("Total of " + str(len(doisEng)) + "article from EN package")
toRemove = []
for i, d in enumerate(dois):
    if d not in doisEng:
        toRemove.append(i)
        print(i)
print("Number of non english article: " + str(len(toRemove)))

#   find missed (new) english article
toAdd = []
for i, d in enumerate(doisEng):
    if d not in dois:
        toAdd.append(i)
print("Found " + str(len(toAdd)) + " new articles")

#   remove non english article
abs = abs.drop(abs.index[toRemove])
print("Total english articles: " + str(len(abs)))

# #   add new found article
# for d in toAdd:
#     s1 = HTMLSession()
#     r1 = s1.get(link)
#     r1.html.render(timeout=120)
#     time.sleep(0.5)
#     soup1 = BeautifulSoup(r1.content, 'html.parser')
#     s1.close()
#
#     title1 = soup1.select("h1[class*='article-title']")
#     if soup1.find('h2', text='Abstract') is not None:
#         text = soup1.find('h2', text='Abstract').next_sibling
#         text = text.get_text(" ")
#     elif soup1.find('h2', text='Introduction') is not None:
#         text = soup1.find('h2', text='Introduction').next_sibling
#         text = text.get_text(" ")
#     else:
#         text = ''
#     pdf = soup1.select('a[href*=".pdf"]')
#     if len(pdf) != 0:
#         pdf = pdf[0]['href']
#     else:
#         pdf = ''

abs.to_csv(r'abstracts-springer-EN.txt', sep='\t', mode='w')
