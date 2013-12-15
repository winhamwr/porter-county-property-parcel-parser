
import requests
from bs4 import BeautifulSoup
from mechanize import Browser

import json
import logging
import os
import os.path
from urlparse import urljoin

logger = logging.getLogger('pcppp')
logger.setLevel(logging.INFO)

RESULTS_DIR = 'results'


class ParcelDetail(object):
    def __init__(self, base_url, parcel_number, detail_content):
        self.base_url = base_url
        self.parcel_number = parcel_number

        self._build_attributes(detail_content)

    def _build_attributes(self, detail_content):
        soup = BeautifulSoup(detail_content)

        record_card_pdf_a = soup.find('a', text='Click here.')
        self.record_card_pdf_url = urljoin(
            self.base_url,
            record_card_pdf_a['href'],
        )

        details_pdf_a = soup.find('a', text='Click here to print.')
        self.details_pdf_url = urljoin(
            self.base_url,
            details_pdf_a['href'],
        )

        property_class_th = soup.find('th', text='Property Class:')
        property_class_td = property_class_th.find_next('td')
        self.property_class = property_class_td.get_text()


class ParcelSearchPage(object):
    BASE_SEARCH_URL = 'http://www.xsoftin.com/porter/parcelsearch.aspx'
    FORM_NAME = 'aspnetForm'
    PROPERTY_CLASS_FIELD = 'ctl00$BodyContent$ddlPropClass'
    PROPERTY_CLASS_EXEMPT_VALUE = 'Exempt'
    PAGE_NUM_FIELD_ID = 'ctl00_BodyContent_GridViewParcelSearchResults_ctl28_PageDropDownList'  # NOQA
    PAGE_NUM_FIELD_NAME = 'ctl00$BodyContent$GridViewParcelSearchResults$ctl28$PageDropDownList'  # NOQA
    RESULTS_TABLE_ID = 'ctl00_BodyContent_GridViewParcelSearchResults'
    RESULT_SELECTION_FIELD_NAME = 'ctl00$BodyContent$GridViewParcelSearchResults'  # NOQA
    RESULTS_PER_PAGE = 25

    def __init__(self, browser):
        self.browser = browser

    def get_exempt_parcel_response(self):
        logger.info("Loading parcel search page")
        self.browser.open(self.BASE_SEARCH_URL)
        self.browser.select_form(self.FORM_NAME)

        # Set the property class drop-down to Exempt
        property_class = self.browser.form.find_control(
            self.PROPERTY_CLASS_FIELD,
        )
        property_class.value = [self.PROPERTY_CLASS_EXEMPT_VALUE]

        logger.info("Retrieving %s parcels", self.PROPERTY_CLASS_EXEMPT_VALUE)
        response = self.browser.submit()

        return response

    def get_response_for_page(self, page_number):
        logger.info("Loading search results page %s", page_number)
        self.browser.select_form(self.FORM_NAME)

        # Set the page number drop-down to the appropriate page number
        page_control = self.browser.form.find_control(
            self.PAGE_NUM_FIELD_NAME,
        )
        page_control.value = [str(page_number)]

        response = self.browser.submit()

        return response

    def build_parcel_details(
        self,
        result_content,
        previously_parsed_parcels=None,
    ):
        """
        The search results are in the RESULTS_TABLE_ID table
        as rows with:
            * A header row.
            * Up to RESULTS_PER_PAGE parcels
            * 2 footer rows

        Each actual result row consists of 3 columns:
            * Link field
            * Parcel number
            * Street Address
            * Parcel owner's name

        The link field contains a javascript action
        to post with a value in the RESULTS_SELECTION_FIELD_NAME field
        with a value corresponding to the row number,
        like ``Select$0``.
        """
        soup = BeautifulSoup(result_content)
        results_table = soup.find(id=self.RESULTS_TABLE_ID)

        results_rows = results_table.find_all('tr')
        # We don't care about the header row or two footer rows
        parcel_rows = results_rows[1:-2]

        result_objects = []
        for i, row in enumerate(parcel_rows):
            selector = 'Select$%s' % i

            tds = row.find_all('td')
            assert len(tds) == 4
            parcel_number_td = tds[1]
            parcel_number = parcel_number_td.get_text()

            if parcel_number in previously_parsed_parcels:
                logger.info(
                    "Previously Parsed Parcel Peeped: %s",
                    parcel_number,
                )
                logger.info("Proceeding.")
                # We've already accounted for this one. No need to do it again.
                continue

            logger.info("Retrieving details on parcel %s", parcel_number)

            self.browser.select_form(self.FORM_NAME)
            # Set the appropriate result selection (normally done via
            # javascript)
            # __EVENTTARGET and __EVENTARGUMENT are goofy asp.net
            # things
            self.browser.form.new_control(
                'input',
                '__EVENTTARGET',
                {'value': self.RESULT_SELECTION_FIELD_NAME},
            )
            self.browser.form.new_control(
                'input',
                '__EVENTARGUMENT',
                {'value': selector},
            )
            self.browser.form.fixup()

            response = self.browser.submit()

            result_objects.append(
                ParcelDetail(
                    base_url=response.geturl(),
                    parcel_number=parcel_number,
                    detail_content=response.read(),
                ),
            )

            self.browser.back()

        return result_objects

    def get_current_page_num(self, content):
        soup = BeautifulSoup(content)
        page_num_selection = soup.find(id=self.PAGE_NUM_FIELD_ID)

        selected_option = page_num_selection.find('option', selected=True)
        if not selected_option:
            logger.critical("No page option currently selected.")
            exit(1)

        return int(selected_option['value'])

    def get_max_page_num(self, content):
        soup = BeautifulSoup(content)
        page_num_selection = soup.find(id=self.PAGE_NUM_FIELD_ID)

        page_options = page_num_selection.find_all('option')

        page_numbers = [int(po['value']) for po in page_options]

        return max(page_numbers)


def main():
    b = Browser()
    search_page = ParcelSearchPage(browser=b)

    previously_parsed_parcels = set()
    try:
        with open(
            os.path.join(
                RESULTS_DIR,
                'previously-parsed-parcels.txt',
            ),
            'r',
        ) as previously_parsed_f:
            data_s = previously_parsed_f.read()
            try:
                data = json.loads(data_s)
                previously_parsed_parcels = set(
                    data['previously-parsed-parcels'],
                )
                logger.info(
                    "Loaded %s previously-parsed-parcels",
                    len(previously_parsed_parcels),
                )
            except ValueError:
                logger.warning(
                    "Couldn't parse JSON from previously-parsed-parcels",
                )
    except IOError:
        logger.info(
            "No previously-parsed-parcels found. Starting from scratch.",
        )

    # Perform the search for `Exempt` parcels
    search_response = search_page.get_exempt_parcel_response()

    content = search_response.read()

    max_page_num = search_page.get_max_page_num(content)
    logger.info("Found %s pages of results", max_page_num)

    current_page_num = search_page.get_current_page_num(content)

    while current_page_num <= max_page_num:
        logger.info(
            "Beginning parcel classification for page %s",
            current_page_num,
        )
        response = search_page.get_response_for_page(current_page_num)
        content = response.read()

        parcel_details = search_page.build_parcel_details(
            content,
            previously_parsed_parcels,
        )

        for parcel in parcel_details:
            if '685' in parcel.property_class:
                logger.info(
                    "Downloading PDFs for parcel of category 685: Parcel %s",
                    parcel.parcel_number,
                )
                parcel_dir = os.path.join(RESULTS_DIR, parcel.parcel_number)
                if not os.path.isdir(parcel_dir):
                    os.makedirs(parcel_dir)

                # Download the record card
                path = os.path.join(
                    parcel_dir,
                    'record-card.pdf',
                )
                r = requests.get(parcel.record_card_pdf_url, stream=True)
                if r.status_code != 200:
                    logger.critical("Broken record-card.pdf link.")
                    exit(1)
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)

                # Download the details
                path = os.path.join(
                    parcel_dir,
                    'detail.html',
                )
                r = requests.get(parcel.details_pdf_url, stream=True)
                if r.status_code != 200:
                    logger.critical("Broken detail.html link.")
                    exit(1)
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
            else:
                logger.info("Parcel doesn't match: %s", parcel.parcel_number)

            previously_parsed_parcels.add(parcel.parcel_number)

        logger.info("Marking pages parcels as parsed")
        with open(
            os.path.join(
                RESULTS_DIR,
                'previously-parsed-parcels.txt',
            ),
            'w',
        ) as ppp_f:
            data = {
                'previously-parsed-parcels': list(previously_parsed_parcels),
            }
            data_j = json.dumps(data)
            ppp_f.write(data_j)

        current_page_num += 1

    logger.info("Successfully classified all %s pages", max_page_num)

if __name__ == "__main__":
    timed_formatter = logging.Formatter(
        "%(asctime)s%(levelname)s:%(message)s", "%M:%S"
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(timed_formatter)

    logger.addHandler(console_handler)

    main()
