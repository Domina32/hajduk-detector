from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import json
import os
import re

url = "https://hajduk.hr/utakmice/raspored"


def parse_date_months(text: str) -> str:
    rep = {
        "siječnja": "01",
        "veljače": "02",
        "ožujka": "03",
        "travnja": "04",
        "svibnja": "05",
        "lipnja": "06",
        "srpnja": "07",
        "kolovoza": "08",
        "rujna": "09",
        "listopada": "10",
        "studenog": "11",
        "prosinca": "12",
    }

    rep = dict((re.escape(k), v) for k, v in rep.items())
    pattern = re.compile("|".join(rep.keys()))

    return pattern.sub(lambda m: rep[re.escape(m.group(0))], text)


def parse_date_days(text: str) -> str:
    rep = {
        "1": "01",
        "2": "02",
        "3": "03",
        "4": "04",
        "5": "05",
        "6": "06",
        "7": "07",
        "8": "08",
        "9": "09",
    }

    if len(text) == 1:
        rep = dict((re.escape(k), v) for k, v in rep.items())
        pattern = re.compile("|".join(rep.keys()))

        return pattern.sub(lambda m: rep[re.escape(m.group(0))], text)

    return text


options = Options()
options.add_argument("--headless")  # type: ignore
browser = Chrome(options=options)

browser.get(url)
browser.implicitly_wait(10)

browser.find_element(By.CLASS_NAME, "cookie-popup__close").click()

data: list[dict[str, str]] = []

schedule_div = browser.find_element(By.ID, "raspored")
print(schedule_div.text.split("\n"))

for element in browser.find_elements(By.CLASS_NAME, "disabled"):
    teams_and_location, date_time = (
        element.text.split("\n")[1].split("   ")[0].split(", ")
    )

    just_time = date_time.split(" ")[3][:-1] + ":00Z"
    partially_parsed_date = parse_date_months(date_time.split(" u ")[0]).split(".")[
        ::-1
    ]
    just_date = (
        partially_parsed_date[0].strip()
        + "-"
        + parse_date_days(partially_parsed_date[1])
    )

    date_time_parsed = "2024-" + just_date + "T" + just_time

    index = 1
    for i, character in enumerate(teams_and_location):
        if character.islower():
            index = i
            break

    teams = teams_and_location[: index - 1]
    location = teams_and_location[index - 1 :]

    entry = {"teams": teams, "location": location, "datetime": date_time_parsed}
    data.append(entry)

json_path = "/home/animod/Git/hajduk-detector/app/src/mocks"
json_name = "scraped.json"
with open(os.path.join(json_path, json_name), "w") as f:
    json.dump(data, f)


browser.close()
input("press any key to exit")
