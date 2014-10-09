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
import time
import traceback
import datetime
import io
import re
import lxml
from lxml import etree, cssselect, html

def main():
    start_time = time.time()
    for name, url, pattern in get_urls():
        page = download_page(name, url)
        links = scrape_links(page, url)
        download_linked_files(name, links, pattern)
    print('Time: {:.0f} seconds.'.format(time.time() - start_time))

def get_urls(url_list='urls.blur'):
    """Get the url-list from a file; return list of name/url tuples."""
    with open(os.path.join('..', 'data', url_list), 'r') as f:
        urls = [tuple(line.split('\t')) for line in f.read().split('\n') 
                if line and line[0] != '#']
    return urls

def download_page(name=None, url=None):
    """Download page, save it with timestamp in the name, return content."""
    if name and url:
        timestamp = construct_date()
        filename = name + '_' + timestamp + '.html'
        os.system('wget ' + url + ' -O ' + os.path.join('..', 'html', filename))
        with open(os.path.join('..', 'html', filename), 'rb') as f:
            page = f.read()
        print('done with page {}'.format(url))
        return page

def download_linked_files(name=None, links=None, pattern=None):
    """Download all linked-to files, save w/ name and timestamp in filenames."""
    if name and links and pattern:
        record_of_download = ['Tab-delimited record of information for each file. item 0: link; item 1: st_size; item 2: mtime converted to human-readable']
        timestamp = construct_date()
        for link in links:
            extension = link.split('.')[-1]
            if extension not in ['html', 'pdf']:
                print('Unknown extension:', extension, ' in link:', link)
                sys.exit()
            # Isolate the file-number of the linked-to file within its title.
            file_no = re.sub(pattern, r'\1', link)
            filename = name + '_' + file_no + '_' + timestamp + '.' + extension
            # Download file and convert to text. 
            # (Only wget succeeds with some servers; urllib.request is blocked.)
            os.system('wget ' + link + ' -O ' + 
                      os.path.join('..', extension, filename))
            os.system('pdftotext ' + os.path.join('..', extension, filename))
            # Find original size and modification time and save this info.
            (_, _, _, _, _, _, st_size, _, mtime, _) = os.stat(
                    os.path.join('..', extension, filename))
            filename = filename.replace('.' + extension, '.txt')
            print('    new filename:', filename)
            os.system('mv ' + os.path.join('..', extension, filename) + ' ' +
                    os.path.join('..', 'txt/'))
            record_of_download.append(
                    link + '\t' + str(st_size) + '\t' + 
                    convert_from_unixtime(mtime))
            print('record:', record_of_download[-1])
        print('done, {} {}'.format(name, timestamp))
        record_of_download = '\n'.join(record_of_download)
        with open(os.path.join(
                '..', 'indexes', 'download_data_' + name + '_' + timestamp + 
                '.txt'), 'w') as f:
            f.write(record_of_download)
    
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

def convert_from_unixtime(unixtime, with_time=True):
    """Convert Unix time to human-readable string."""
    if not with_time:
        # Date only, no time.
        date = datetime.datetime.fromtimestamp(
            unixtime).strftime('%Y%m%d')
    else:
        # Both date and time.
        date = datetime.datetime.fromtimestamp(
            unixtime).strftime('%Y%m%d-%H%M')
    return date
