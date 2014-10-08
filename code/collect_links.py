#! /usr/bin/env python
# collect_links.py
# David Prager Branner
# 20141008

"""Download a malformed page of links, scrape it, and save the data to disk.

Dependencies:
    brew install xpdf
    pip install lxml cssselect

We expect the web page to be a series of links to PDF files, and the PDF files to contain lists of phone numbers. It is these phone numbers that are to be saved to disk.
"""

import sys
import os
import traceback
import datetime
import io
import lxml
from lxml import etree, cssselect, html

def main():
    for name, url in get_urls():
        page = download(name, url)
        links = scrape_links(page, url)
        print(links)

def get_urls():
    """Get the url-list from a file; return list of name/url tuples."""
    with open(os.path.join('..', 'data', 'urls.blur'), 'r') as f:
        urls = [tuple(line.split('\t')) for line in f.read().split('\n') 
                if line and line[0] != '#']
    return urls

def download(name=None, url=None):
    """Download page, save it with timestamp in the name, return content."""
    if name and url:
        timestamp = construct_date()
        filename = name + '_' + timestamp + '.html'
        os.system('wget ' + url + ' -O ' + os.path.join('..', 'html', filename))
        with open(os.path.join('..', 'html', filename), 'rb') as f:
            page = f.read()
        return page

def scrape_links(page=None, url=None):
    """Return all links found in the page."""
    if page and url:
        parser = lxml.etree.HTMLParser(recover=True)
        root = None
        try:
            root = lxml.etree.parse(io.BytesIO(page), parser)
        except lxml.etree.XMLSyntaxError:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        page_parsed = html.fromstring(page)
        selector = cssselect.CSSSelector("a")
        links = [element.get('href') for element in selector(page_parsed)]
        links.sort()
        # Prepend URI if not already present.
        links = [os.path.join(url, link) 
                 if link[:4] != 'http' else link
                 for link in links]
        return links
    
def construct_date(date_and_time=None):
    """Construct a time-and-date string for appending to a filename."""
    if not date_and_time:
        date_and_time = datetime.datetime.today()
    date_and_time = date_and_time.strftime('%Y%m%d-%H%M')
    return date_and_time

