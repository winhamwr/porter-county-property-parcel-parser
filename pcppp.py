
from bs4 import BeautifulSoup
from mechanize import Browser

import logging

logger = logging.getLogger('pcppp')
logger.setLevel(logging.INFO)


class ParcelSearchPage(object):
    BASE_SEARCH_URL = 'http://www.xsoftin.com/porter/parcelsearch.aspx'
    FORM_NAME = 'aspnetForm'
    PROPERTY_CLASS_FIELD = 'ctl00$BodyContent$ddlPropClass'
    PROPERTY_CLASS_EXEMPT_VALUE = 'Exempt'
    PAGE_NUM_FIELD_ID = 'ctl00_BodyContent_GridViewParcelSearchResults_ctl28_PageDropDownList'  # NOQA
    PAGE_NUM_FIELD_NAME = 'ctl00$BodyContent$GridViewParcelSearchResults$ctl28$PageDropDownList' # NOQA

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
        property_class.value = [str(page_number)]

        response = self.browser.submit()

        return response

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

    # Load the already-parsed-parcels.txt file
    # Store those parcels as already-finished

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

        import ipdb; ipdb.set_trace()
        # Get the `Parcel Number`

        # If this number is already in the already-finished, skip it

        # If it's new, visit the parcel page
            # Determine if `685` is in the property class
            # if it is
                # Determine the `Parcel Number`
                # Create a folder with that name
                # Download both PDFs and put them in that folder
            # Add the parcel number to the already-parsed-parcels.txt file
            # Hit the back button

        current_page_num += 1

    logger.info("Successfully classified all %s pages", max_page_num)

if __name__ == "__main__":
    main()
