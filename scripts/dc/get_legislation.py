#!/usr/bin/env python

# DC legislation scraper by Keith Ivey <keith@iveys.org>, based on
# scraper for NC by Jame Turk, 2009-04-01
#
# I'm not sure what the best way to handle the chamber is for DC, 
# since the council is unicameral.  The same issue will arise for
# Nebraska.  I treated DC as having an upper chamber but no lower.

import urllib
from BeautifulSoup import BeautifulStoneSoup
import datetime
import re

# ugly hack
import sys
sys.path.append('./scripts')
from pyutils.legislation import LegislationScraper, NoDataForYear

def clean_legislators(s):
    s = s.replace('&nbsp;', ' ').strip()
    return [l.strip() for l in s.split(';') if l]

class DCLegislationScraper(LegislationScraper):

    state = 'dc'

    def get_bill_info(self, session, bill_id):
        bill_detail_url = 'http://www.ncga.state.nc.us/gascripts/BillLookUp/BillLookUp.pl?Session=%s&BillID=%s' % (session, bill_id)

        # parse the bill data page, finding the latest html text
        if bill_id[0] == 'H':
            chamber = 'lower'
        else:
            chamber = 'upper'

        bill_data = urllib.urlopen(bill_detail_url).read()
        bill_soup = BeautifulSoup(bill_data)

        bill_title = bill_soup.findAll('div', style="text-align: center; font: bold 20px Arial; margin-top: 15px; margin-bottom: 8px;")[0].contents[0]

        self.add_bill(chamber, session, bill_id, bill_title)

        # get all versions
        links = bill_soup.findAll('a')
        for link in links:
            if link.has_key('href') and link['href'].startswith('/Sessions') and link['href'].endswith('.html'):
                version_name = link.parent.previousSibling.previousSibling.contents[0].replace('&nbsp;', ' ')
                version_url = 'http://www.ncga.state.nc.us' + link['href']
                self.add_bill_version(chamber, session, bill_id, version_name, version_url)

        # grab primary and cosponsors from table[6]
        tables = bill_soup.findAll('table')
        sponsor_rows = tables[6].findAll('tr')
        sponsors = clean_legislators(sponsor_rows[1].td.contents[0])
        for leg in sponsors:
            self.add_sponsorship(chamber, session, bill_id, 'primary', leg)
        cosponsors = clean_legislators(sponsor_rows[2].td.contents[0])
        for leg in cosponsors:
            self.add_sponsorship(chamber, session, bill_id, 'cosponsor', leg)

        # easier to read actions from the rss.. but perhaps favor less HTTP requests?
        rss_url = 'http://www.ncga.state.nc.us/gascripts/BillLookUp/BillLookUp.pl?Session=%s&BillID=%s&view=history_rss' % (session, bill_id)
        rss_data = urllib.urlopen(rss_url).read()
        rss_soup = BeautifulSoup(rss_data)
        # title looks like 'House Chamber: action'
        for item in rss_soup.findAll('item'):
            action = item.title.contents[0]
            pieces = item.title.contents[0].split(' Chamber: ')
            if len(pieces) == 2:
                action_chamber = pieces[0]
                action = pieces[1]
            else:
                action_chamber = None
                action = pieces[0]
            date = item.pubdate.contents[0]
            self.add_action(chamber, session, bill_id, action_chamber, action, date)

    def scrape_session(self, chamber, session):

        url = 'http://dccouncil.us/lims/print/' + \
            'list.aspx?FullPage=True&Period=%d' % session

        self.be_verbose("Downloading %s" % url)
        data = urllib.urlopen(url).read()
        soup = BeautifulStoneSoup(data,
            convertEntities=BeautifulStoneSoup.HTML_ENTITIES)

        rows = soup.find(id='DataGrid').findAll('tr')[1:]
        for row in rows:
            cells = row.findAll('td')
            bill_id = cells[0].contents[0]
            bill_title = cells[1].contents[0]
            bill_title = bill_title.replace(u'\u2019', "'")
            bill_title = bill_title.replace(u'\u00a0', ' ')
            bill_title = re.sub(r'^"(.*)"\.?\s*$', r'\1', bill_title)
            bill_title = re.sub(r'\s+', ' ', bill_title)
            self.add_bill(chamber, session, bill_id, bill_title)

    def scrape_bills(self, chamber, year):

        if int(year) < 1999 or int(year) > datetime.date.today().year or \
            int(year) % 2 == 0:
                raise NoDataForYear(year)

        session = (int(year) - 1973) / 2
        self.scrape_session(chamber, session)

if __name__ == '__main__':
    DCLegislationScraper().run()
