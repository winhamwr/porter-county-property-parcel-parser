
from mechanize import Browser

# Get the total number of pages

# Loop t


class ParcelSearchPage(object):
    BASE_SEARCH_URL = 'http://www.xsoftin.com/porter/parcelsearch.aspx'
    FORM_NAME = 'aspnetForm'
    PROPERTY_CLASS_FIELD = 'ctl00$BodyContent$ddlPropClass'
    PROPERTY_CLASS_EXEMPT_VALUE = 'Exempt'

    def __init__(self, browser):
        self.browser = browser

    def get_exempt_parcel_results(self):
        self.browser.open(self.BASE_SEARCH_URL)
        self.browser.select_form(self.FORM_NAME)

        # Set the property class drop-down to Exempt
        property_class = self.browser.form.find_control(
            self.PROPERTY_CLASS_FIELD,
        )
        property_class.value = [self.PROPERTY_CLASS_EXEMPT_VALUE]

        response = self.browser.submit()

        content = response.read()
        import ipdb; ipdb.set_trace()

        return content

def main():
    b = Browser()
    search_page = ParcelSearchPage(browser=b)

    # Load the already-parsed-parcels.txt file
    # Store those parcels as already-finished

    # Perform the search for `Exempt` parcels
    search_results = search_page.get_exempt_parcel_results()

    # Loop through the search results
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

    # If there is another page of results, go to that



