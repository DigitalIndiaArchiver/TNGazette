"""
Tamil Nadu Gazette Archiver

This program scrapes data from the Tamil Nadu Stationery and Printing Department's website to archive the Tamil Nadu gazettes. The gazettes are available on the website in PDF format, and the program extracts the links to the gazettes and stores them in a CSV file. The program also archives the gazette links using the Wayback Machine API.

Functions:
----------
table_to_dataframe(url, url_base)
    Extracts the table from the given URL and returns it as a pandas dataframe.

extract_extraordinary_gazette(extraordinary_url)
    Extracts the extraordinary gazette from the given URL and returns it as a pandas dataframe.

extract_gazatte_issue_dataframes(url)
    Extracts the gazette issues from the given URL and returns them as a pandas dataframe.

extract_gazette_dataframe(url)
    Extracts the gazette data from the given URL and returns it as a pandas dataframe.

wayback_archival(df, url_col)
    Archives the URLs in the given dataframe using the Wayback Machine API and returns the updated dataframe.

Main program:
-------------
The program scrapes the Tamil Nadu Stationery and Printing Department's website to archive the Tamil Nadu gazettes.
The gazettes are available on the website in PDF format, and the program extracts the links to the gazettes and stores them in a CSV file.
The program also archives the gazette links using the Wayback Machine API.

Usage:
------
The program can be run from the command line as follows:
    python tn_gazette_archiver.py
"""


import argparse
from datetime import datetime
from enum import Enum

import pandas as pd
import requests
import waybackpy
from bs4 import BeautifulSoup
from waybackpy import WaybackMachineAvailabilityAPI, WaybackMachineSaveAPI


class ArchiveMode(Enum):
    CURRENT_YEAR = 0
    FULL = 1


SITE_URL = "http://www.stationeryprinting.tn.gov.in"
GAZETTE_BASE_URL = SITE_URL + "/gazette"
EXTRAORDINARY_BASE_URL = SITE_URL + "/extraordinary/"
GAZETTE_PAGE_URL = GAZETTE_BASE_URL + "/gazette_list"
EXTRAORDINARY_PAGE_URL = EXTRAORDINARY_BASE_URL + "extraord_list"
EXTENSION = ".php"


def wayback_archival(df, url_col):
    """
    Wayback archival of URL columns in dataframe
    """
    archived_urls = []
    archived_dates = []

    for url in df[url_col]:
        user_agent = "Python Archiver"
        cdx_api = waybackpy.WaybackMachineCDXServerAPI(url, user_agent)
        save_url = False
        try:
            oldest_snapshot = cdx_api.oldest()

            if oldest_snapshot:
                archived_urls.append(oldest_snapshot.archive_url)
                archived_dates.append(pd.to_datetime(
                    oldest_snapshot.timestamp, format='%Y%m%d%H%M%S'))
            else:
                save_url = True
        except waybackpy.exceptions.NoCDXRecordFound:
            save_url = True
        if save_url:
            try:
                save_api = waybackpy.WaybackMachineSaveAPI()
                response = save_api.save(url)

                if response.status_code == 200:
                    archive_url = f"https://web.archive.org/web/{url}"
                    archived_urls.append(archive_url)
                    archived_dates.append(pd.Timestamp.utcnow().floor('s'))
                else:
                    archived_urls.append(None)
                    archived_dates.append(None)
            except:
                archived_urls.append(None)
                archived_dates.append(None)

    df['Archived URL'] = archived_urls
    df['Archived Date'] = archived_dates

    return df


def table_to_dataframe(url, url_base):
    """
    Extracts a table from a webpage and returns it as a pandas DataFrame.

    Parameters:
        url (str): The URL of the webpage containing the table to extract.
        url_base (str): The base URL of the webpage.

    Returns:
        pandas.DataFrame: A DataFrame containing the contents of the table.

    Raises:
        ValueError: If no tables are found on the webpage.
    """

    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", attrs={'border': '1'})

    # Convert the HTML table to a Pandas dataframe
    df = pd.read_html(str(table))[0]
    df = df.drop(index=0).reset_index(drop=True)

    # Extract the links from the table and add them as a new column
    links = []
    for row in table.find_all("tr")[1:]:
        link = row.find("a")
        if link:
            links.append(url_base + link.get("href"))
        else:
            links.append('')
    df["Link"] = links

    return df


def extract_extraordinary_gazette(extraordinary_url):
    df = table_to_dataframe(url=extraordinary_url,
                            url_base=EXTRAORDINARY_BASE_URL)
    df.columns = ["Issue No", "Issue Date",
                  "Gazette Number", "Category", "Department", "URL"]
    # Convert "Issue Date" column to datetime format
    df["Issue Date"] = pd.to_datetime(df["Issue Date"], format="%d-%m-%Y")
    return df


def extract_gazatte_issue_dataframes(url):
    issues_df = table_to_dataframe(url, url_base=GAZETTE_BASE_URL + "/")
    issues_df.columns = ["Issue No and Date", "Particulars", "URL"]
    return issues_df


def extract_gazette_dataframe(url):
    gazatte_df = table_to_dataframe(url, url_base=GAZETTE_BASE_URL)
    gazatte_df.columns = ["Part", "Content", "URL"]
    return gazatte_df


def url_exists(url):
    s = requests.Session()
    a = requests.adapters.HTTPAdapter(max_retries=3)
    b = requests.adapters.HTTPAdapter(max_retries=3)
    s.mount('http://', a)
    s.mount('https://', b)
    r = s.get(url, stream=True)
    if r.status_code == 200:
        return False
    else:
        return True


def main(archive_mode):

    extraordinary_dataframes = []
    gazette_dataframes = []
    gazatte_issues_dataframes = []
    years = ['']

    if archive_mode == ArchiveMode.FULL:
        years.extend(list(map(str, range(2008, 2023))))

    for year in years:
        extraordinary_url = f"{EXTRAORDINARY_PAGE_URL}{year}{EXTENSION}"
        gazette_url = f"{GAZETTE_PAGE_URL}{year}{EXTENSION}"
        extraordinary_dataframes.append(
            extract_extraordinary_gazette(extraordinary_url))

        issue_dataframe = extract_gazatte_issue_dataframes(gazette_url)
        gazatte_issues_dataframes.append(issue_dataframe)

        for idx, series in issue_dataframe.iterrows():
            gazette_dataframe = extract_gazette_dataframe(series['URL'])
            gazette_dataframe['Date'] = pd.to_datetime(
                series['Issue No and Date'][-10:].strip(), format="%d-%m-%Y")
            gazette_dataframe['Issue'] = series['Issue No and Date'].split(
                '-')[0].strip()
            gazette_dataframes.append(gazette_dataframe)

    extraordinary_dataframes = pd.concat(
        extraordinary_dataframes, ignore_index=True)
    gazatte_issues_dataframes = pd.concat(
        gazatte_issues_dataframes, ignore_index=True)
    gazette_dataframes = pd.concat(gazette_dataframes, ignore_index=True)

    gazette_dataframes = gazette_dataframes.sort_values(
        by='Date', ascending=False)

    gazette_dataframes['Deleted'] = gazette_dataframes.apply(
        lambda row: url_exists(row.URL), axis=1)
    extraordinary_dataframes['Deleted'] = extraordinary_dataframes.apply(
        lambda row: url_exists(row.URL), axis=1)

    if archive_mode == ArchiveMode.CURRENT_YEAR:
        extraordinary_dataframes = wayback_archival(
            extraordinary_dataframes, url_col="URL")
        gazette_dataframes = wayback_archival(
            gazette_dataframes, url_col="URL")
        extraordinary_dataframes.to_csv(
            f'data/ExtraOrdinaryGazattes_{str(datetime.today().year)}.csv')
        gazatte_issues_dataframes.to_csv(
            f'data/GazatteIssues_{str(datetime.today().year)}.csv')
        gazette_dataframes.to_csv(
            f'data/Gazattes_{str(datetime.today().year)}.csv')
    else:
        extraordinary_dataframes.to_csv('data/ExtraOrdinaryGazattes.csv')
        gazatte_issues_dataframes.to_csv('data/GazatteIssues.csv')
        gazette_dataframes.to_csv('data/Gazattes.csv')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-mode", type=str, choices=[
                        "full", "current-year"], default="current-year", help="The archive mode")

    args = parser.parse_args()
    archive_mode = args.archive_mode
    if archive_mode == "full":
        archive_mode = ArchiveMode.FULL
    else:
        archive_mode = ArchiveMode.CURRENT_YEAR
    main(archive_mode)
