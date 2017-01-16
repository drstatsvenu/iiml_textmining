""".."""

from __future__ import print_function
from bs4 import BeautifulSoup as bs
import requests
import traceback
import json
import re
import pandas as pd
import numpy as np


def json2df(fname, year):
    with open(fname, "r") as f_in:
        orgData = json.load(f_in)
    cleanTitles = {}
    pattern = "[0-9]+\."
    for k, v in orgData.items():
        title = re.sub(pattern, "", k.lstrip().rstrip())
        cleanTitles[title.lstrip().rstrip()] = v
    df = pd.DataFrame(index=cleanTitles.keys())
    for key in v.keys():
        df[key] = ""
    for ix, rowData in df.iterrows():
        propData = cleanTitles[ix]
        for k, v in propData.items():
            if k != "comments":
                rowData.loc[k] = v
    df.columns = [c.lower().replace(" ", "_").replace(":", "") for c in df]
    df['n_comments'] = df.pop('comments')
    for ix, rowdata in df.iterrows():
        rowdata.loc["n_comments"] = len(cleanTitles[ix]['comments'])
    df['n_comments'] = df['n_comments'].astype(int)
    df['n_votes'] = df['n_votes'].astype(int)
    df['year'] = year
    for col in df:
        if df[col].dtype is np.dtype('O'):
            df[col] = df.pop(col).apply(lambda x: x.lstrip().rstrip())
    return df


def make_request(url):
    """Make an HTTP GET request and return data in beautiful soup.

    :param url: URL to be scraped.
    """
    headers = {}
    headers['User-Agent'] = ("Mozilla/5.0 (Macintosh; Intel Mac"
                             " OS X 10_11_5) AppleWebKit/537.36"
                             "(KHTML, like Gecko) Chrome/51.0."
                             "2704.103 Safari/537.36")
    r = requests.get(url, headers=headers)
    return bs(r.text)


def scrape(url, base_url="https://in.pycon.org"):
    result = {}
    soup = make_request(url)
    soup_proposals = soup.findAll(
        'div', attrs={'class': 'row user-proposals'})
    for proposal in soup_proposals:
        p = proposal.find('h3', attrs={'class': 'proposal--title'})
        title, url = p.text, "".join([base_url,
                                      p.find('a').get('href', '')])
        soup = make_request(url)
        if not soup:
            continue
        soup_proposal = soup.findAll(
            'div', attrs={'class': 'proposal-writeup--section'})
        temp = {}
        for data in soup_proposal:
            try:
                temp[data.find('h4').text] = "".join(
                    [ptag.text for ptag in data.findAll('p')])
            except:
                print(traceback.format_exc())
        temp['comments'] = []
        for comment in soup.findAll("div", attrs={'class': 'comment-description'}):
            text = comment.find("span")
            if text:
                temp['comments'].append(dict(
                    text=text.text.strip(),
                    by=comment.find('b').text.strip(),
                    time=comment.find('small').text.strip()))
        talk_details = soup.findAll('tr')
        for section in talk_details:
            row = section.findAll('td')
            temp[row[0].text] = row[1].text
        vCount = soup.findAll('h1', attrs={'class': 'vote-count'})[0]
        temp["n_votes"] = int(vCount.text.lstrip().rstrip())
        result[title] = temp
        return result

if __name__ == '__main__':
    cfp_2015_url = "https://in.pycon.org/cfp/pycon-india-2015/proposals/"
    cfp_2016_url = "https://in.pycon.org/cfp/2016/proposals/"
    results = scrape(cfp_2015_url)
    with open("cfp2015.json", "w") as f_out:
        json.dump(results, f_out)
    results = scrape(cfp_2016_url)
    with open("cfp2016.json", "w") as f_out:
        json.dump(results, f_out)
    df1 = json2df("cfp2015.json", 2015)
    df2 = json2df("cfp2016.json", 2016)
    df = pd.concat((df1, df2), axis=0)
    df.to_csv("cfp.tsv", encoding="utf-8", sep="\t", index_label="title")
