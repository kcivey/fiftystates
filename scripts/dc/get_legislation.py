#!/usr/bin/python

# DC legislation scraper by Keith Ivey <keith@iveys.org>, based on
# scrapers for states by Jame Turk and Rebecca Shapiro, 2009-03-07

# I'm not sure what the best way to handle the chamber is for DC, 
# since the council is unicameral.  The same issue will arise for
# Nebraska.  I treated DC as having an upper chamber but no lower.
#
# Also, scraping by year could lead to redundancy, since DC and lots
# of states have 2-year legislative sessions.  For example, with the
# DC scraper, year 2007 and year 2008 produce the same data because
# they're both council session 17.

import re
import urllib2
import datetime as dt

# ugly hack
import sys
sys.path.append('.')
from pyutils.legislation import run_legislation_scraper

def scrape_legislation(chamber,year):
    assert chamber == 'upper', "DC council is unicameral"   

    assert int(year) >= 1999, "no data available before 1999"
    assert int(year) <= dt.date.today().year, "can't look into the future"

    session = session_number(int(year))

    index_url ='http://dccouncil.us/lims/print/' + \
        'list.aspx?FullPage=True&Period=%s' % session
    req = urllib2.Request(index_url)
    response = urllib2.urlopen(req)
    doc = response.read()
    
    re_str = '>([A-Z]{1,3}\d\d-\d{4})</td>'

    for m in re.finditer(re_str, doc):
        bill_id = m.group(1)
        bill_url = 'http://dccouncil.us/lims/legislation.aspx?LegNo=%s' % \
            bill_id
        yield {'state':'DC','chamber':chamber,'session':session,
               'bill_id':bill_id,'remote_url':bill_url}

# Calculates the session number given the year
def session_number(year):
    return int( ( year - 1973 ) / 2 )

if __name__ == '__main__':
    run_legislation_scraper(scrape_legislation)
