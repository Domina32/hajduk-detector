import re
import json
import os
import sqlite3
from utils.constants import DATABASE_URL


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


def parse_date_and_time(date_time: str):
    time = date_time.split(" ")[3][:-1] + ":00Z"
    partially_parsed_date = parse_date_months(date_time.split(" u ")[0]).split(".")[
        ::-1
    ]
    just_date = (
        partially_parsed_date[0].strip()
        + "-"
        + parse_date_days(partially_parsed_date[1])
    )

    return just_date + "T" + time


def write_to_json(
    data: list[dict[str, str]],
    json_path: str = "/home/animod/Git/hajduk-detector/app/src/mocks",
    json_name: str = "scraped.json",
):
    with open(os.path.join(json_path, json_name), "w") as f:
        json.dump(data, f)


def write_entries_to_database(data: list[dict[str, str]]):
    with sqlite3.connect(DATABASE_URL) as connection:
        cur = connection.cursor()
        values = [
            f'("{entry["teams"]}", "{entry["location"]}", "{entry["datetime"]}"),'
            for entry in data
        ]
        query = f"INSERT INTO games (teams, location, datetime) VALUES {''.join(values)[:-1]};"
        print(query)
        cur.execute(query)
