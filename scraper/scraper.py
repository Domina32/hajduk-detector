from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime
from utils.helpers import (
    write_entries_to_database,
    parse_date_and_time,
)
from utils.constants import SCRAPED_WEBSITE_URL


def scrape():
    """
    Simple scraper of Hajduk games from their website.
    """

    options = Options()
    options.add_argument("--headless")  # type: ignore

    browser = Chrome(options=options)
    browser.get(SCRAPED_WEBSITE_URL)
    browser.implicitly_wait(10)
    browser.find_element(By.CLASS_NAME, "cookie-popup__close").click()

    data: list[dict[str, str]] = []

    schedule_div = browser.find_element(By.ID, "raspored")
    current_year = str(datetime.now().year)

    for element in schedule_div.find_elements(  # type:ignore
        By.CSS_SELECTOR, "#raspored > *"
    ):
        if element.tag_name == "h3":
            current_year = element.text.split(" ")[1][:-1]

        elif element.tag_name == "a":
            teams_and_location, date_time = (
                element.text.split("\n")[1].split("   ")[0].split(", ")
            )

            parsed_date_time = current_year + "-" + parse_date_and_time(date_time)

            index = 1
            for i, character in enumerate(teams_and_location):
                if character.islower():
                    index = i
                    break

            teams = teams_and_location[: index - 1]
            location = teams_and_location[index - 1 :]

            entry = {"teams": teams, "location": location, "datetime": parsed_date_time}
            data.append(entry)

    write_entries_to_database(data)

    browser.close()
    input("press enter to exit")


if __name__ == "__main__":
    scrape()
