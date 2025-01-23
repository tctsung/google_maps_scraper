"""This script serves as an example on how to use Python 
   & Playwright to scrape/extract data from Google Maps"""

from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd
import argparse
import os
import sys
import datetime
from tqdm import tqdm


@dataclass
class Business:
    """
    TODO: holds business data
    """

    name: str = None
    address: str = None
    category: str = None
    reviews_count: int = None
    reviews_average: float = None
    price: str = None
    phone_number: str = None
    website: str = None
    link: str = None
    # latitude: float = None
    # longitude: float = None


@dataclass
class BusinessList:
    """holds list of Business objects,
    and save to both excel and csv
    """

    business_list: list[Business] = field(default_factory=list)
    save_at = "output"

    def dataframe(self):
        """transform business_list to pandas dataframe

        Returns: pandas dataframe
        """
        return pd.json_normalize(
            (asdict(business) for business in self.business_list), sep="_"
        )

    def save_to_excel(self, filename):
        """saves pandas dataframe to excel (xlsx) file

        Args:
            filename (str): filename
        """

        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_excel(f"output/{filename}.xlsx", index=False)

    def save_to_csv(self, filename):
        """saves pandas dataframe to csv file

        Args:
            filename (str): filename
        """

        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_csv(f"output/{filename}.csv", index=False)


# def extract_coordinates_from_url(url: str) -> tuple[float, float]:
#     """helper function to extract coordinates from url"""

#     coordinates = url.split("/@")[-1].split("/")[0]
#     # return latitude, longitude
#     return float(coordinates.split(",")[0]), float(coordinates.split(",")[1])


def main():  # python main.py -s="new york 10003 boutique" -t=10

    ########
    # input
    ########

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str)  # search keyword
    parser.add_argument("-t", "--total", type=int)  # no. of business
    args = parser.parse_args()
    today_date = str(datetime.datetime.now().strftime("%Y_%m_%d"))
    search_for = args.search
    # total number of products to scrape. Default is 10
    if not args.search:
        print("Error occured: You must pass the -s search argument")
        sys.exit()
    if args.total:
        total = args.total
    else:
        total = 1_000_000

    # read search from arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str)
    parser.add_argument("-t", "--total", type=int)
    args = parser.parse_args()
    search_for = args.search
    total = args.total

    ##################
    ## Web-scraping ##
    ##################
    start_time = datetime.datetime.now()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # > headless=True -> will NOT show a user interface
        # > use headless=True in production, faster
        page = browser.new_page()

        page.goto(
            "https://www.google.com/maps", timeout=60000
        )  # 60 sec (unit: milisec)
        page.wait_for_timeout(
            1000
        )  # wait is added for dev phase. can remove it in production

        page.locator('//input[@id="searchboxinput"]').fill(
            search_for
        )  # fill searchbox with ur input
        page.wait_for_timeout(1000)

        page.keyboard.press("Enter")  # press enter
        page.wait_for_timeout(1000)

        # scrolling
        page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

        # this variable is used to detect if the bot
        # scraped the same number of listings in the previous iteration
        previously_counted = 0
        while True:
            page.mouse.wheel(0, 10000)
            page.wait_for_timeout(3000)

            if (
                page.locator(
                    '//a[contains(@href, "https://www.google.com/maps/place")]'
                ).count()
                >= total
            ):
                listings = page.locator(
                    '//a[contains(@href, "https://www.google.com/maps/place")]'
                ).all()[:total]
                listings = [listing.locator("xpath=..") for listing in listings]
                print(f"Total Scraped for {args.search}: {len(listings)}")
                break
            else:
                # logic to break from loop to not run infinitely
                # in case arrived at all available listings
                if (
                    page.locator(
                        '//a[contains(@href, "https://www.google.com/maps/place")]'
                    ).count()
                    == previously_counted
                ):
                    listings = page.locator(
                        '//a[contains(@href, "https://www.google.com/maps/place")]'
                    ).all()
                    print(f"Total Scraped for {args.search}: {len(listings)}")
                    break
                else:
                    previously_counted = page.locator(
                        '//a[contains(@href, "https://www.google.com/maps/place")]'
                    ).count()
                    # print(
                    #     f"Currently Scraped for {args.search}: ",
                    #     page.locator(
                    #         '//a[contains(@href, "https://www.google.com/maps/place")]'
                    #     ).count(),
                    # )

        business_list = BusinessList()

        # scraping
        for listing in (pbar := tqdm(listings)):  # loop through all business
            pbar.set_description(f"Processing {search_for}")
            try:
                listing.click()  # click each business
                page.wait_for_timeout(3000)

                address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
                website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
                phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
                reviews_average_xpath = '//div[@class="F7nice "]/span[1]/span'
                reviews_count_xpath = '//div[@class="F7nice "]/span[2]/span/span'
                # share_link_xpath = '//div[contains(@class,"WVlZT")]/input[contains(@class,"vrsrZe")]'
                category_xpath = (
                    '//div[contains(@class, "fontBodyMedium")]//button[@class="DkEaL "]'
                )
                price_xpath = '//span[@class="mgr77e"]/span/span[2]'
                business = Business()
                name_path = page.title()
                business.name = name_path.split(" - ")[0]

                if page.locator(address_xpath).count() > 0:
                    business.address = page.locator(address_xpath).all()[0].inner_text()
                else:
                    business.address = ""
                if page.locator(website_xpath).count() > 0:
                    business.website = page.locator(website_xpath).all()[0].inner_text()
                else:
                    business.website = ""
                if page.locator(phone_number_xpath).count() > 0:
                    business.phone_number = (
                        page.locator(phone_number_xpath).all()[0].inner_text()
                    )
                else:
                    business.phone_number = ""
                if page.locator(reviews_average_xpath).count() > 0:
                    business.reviews_average = float(
                        page.locator(reviews_average_xpath).all()[0].inner_text()
                    )
                    reviews_count = (
                        page.locator(reviews_count_xpath).all()[0].inner_text()
                    )
                    reviews_count = reviews_count.replace(",", "")[
                        1:-1
                    ]  # turn (8,822) to 8822
                    business.reviews_count = int(reviews_count)
                else:
                    business.reviews_average = None
                    business.reviews_count = None

                # business.latitude, business.longitude = extract_coordinates_from_url(
                #     page.url
                # )

                # get the category info
                if page.locator(category_xpath).count() > 0:
                    business.category = (
                        page.locator(category_xpath).all()[0].inner_text()
                    )
                else:
                    business.category = ""
                # get price
                if page.locator(price_xpath).count() > 0:
                    business.price = page.locator(price_xpath).all()[0].inner_text()
                else:
                    business.price = ""

                ## give up this part because it's causing timeout error
                business.link = page.url
                # share_button_xpath = "button[data-value='Share']"
                # close_button_xpath = '//button[@jsaction="modal.close"]'
                # share_button = page.locator(share_button_xpath)
                # page.wait_for_selector(share_button_xpath)
                # share_button.click()
                # if page.locator(share_link_xpath).count() > 0:
                #     business.link = page.locator(share_link_xpath).get_attribute("value")
                # else:
                #     business.link = ""
                # close_button = page.locator(close_button_xpath)  # close the share button
                # page.wait_for_selector(close_button_xpath)
                # close_button.click()
                business_list.business_list.append(business)
            except Exception as e:
                print(e)

        #########
        # output
        #########
        business_list.save_to_excel(
            f"google_maps_data_{search_for}_{today_date}".replace(" ", "_")
        )
        business_list.save_to_csv(
            f"google_maps_data_{search_for}_{today_date}".replace(" ", "_")
        )
        browser.close()
        print(
            f"Finish scrapping for {args.search} at {datetime.datetime.now()}, time spent: {(datetime.datetime.now() - start_time).seconds/60} minutes"
        )


if __name__ == "__main__":
    main()
