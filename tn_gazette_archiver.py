"""
Tamil Nadu Gazette Archiver

This program scrapes data from the Tamil Nadu Stationery and Printing Department's website to archive the Tamil Nadu gazettes. The gazettes are available on the website in PDF format, and the program extracts the links to the gazettes and stores them in a CSV file. The program also archives the gazette links using the Wayback Machine API.

Functions:
----------
table_to_dataframe(url, url_base)
    Extracts the table from the given URL and returns it as a pandas dataframe.

extract_extraordinary_gazette(year)
    Extracts the extraordinary gazette for the given year and returns it as a pandas dataframe.

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

import base64
import pandas as pd
import requests
import waybackpy
from bs4 import BeautifulSoup
from waybackpy import WaybackMachineAvailabilityAPI, WaybackMachineSaveAPI


class ArchiveMode(Enum):
    CURRENT_YEAR = 0
    FULL = 1


SITE_URL = "https://www.stationeryprinting.tn.gov.in"
GAZETTE_BASE_URL = SITE_URL + "/gazette/"
EXTRAORDINARY_BASE_URL = SITE_URL + "/extraordinary/"
GAZETTE_PAGE_URL = GAZETTE_BASE_URL + "gazette_list"
EXTRAORDINARY_PAGE_URL = SITE_URL + "/extra_ordinary_lists.php"
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
            except Exception:
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


def extract_extraordinary_gazette(year):
    """
    Scrapes extraordinary gazettes for a given year from the new site.

    The redesigned site uses base64-encoded year IDs and embeds PDF links
    inside the 'Extraordinary Part & Section' column (index 2).

    Parameters:
        year (int): The year to scrape.

    Returns:
        pandas.DataFrame: Columns: Issue No, Issue Date, Gazette Number,
            Category, Subject, Department, G.O No, URL
    """
    b64_year = base64.b64encode(str(year).encode()).decode()
    url = f"https://www.stationeryprinting.tn.gov.in/extra_ordinary_lists.php?id={b64_year}"
    print(f'  Fetching extraordinary gazettes for {year}...')
    response = requests.get(url, timeout=30)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table')
    if not table:
        print(f'  No table found for {year}')
        return pd.DataFrame()

    rows = table.find_all('tr')
    data = []
    for row in rows[1:]:
        cells = row.find_all('td')
        if len(cells) >= 7:
            link = cells[2].find('a')
            pdf_link = link.get('href', '') if link else ''
            if pdf_link and not pdf_link.startswith('http'):
                pdf_link = 'https://www.stationeryprinting.tn.gov.in/' + pdf_link.lstrip('/')
            data.append([
                cells[0].get_text(strip=True),   # Issue No
                cells[1].get_text(strip=True),   # Issue Date
                cells[2].get_text(strip=True),   # Extraordinary Part & Section → Gazette Number
                cells[3].get_text(strip=True),   # Extraordinary Type → Category
                cells[4].get_text(strip=True),   # Subject
                cells[5].get_text(strip=True),   # Department
                cells[6].get_text(strip=True),   # G.O No
                pdf_link,                         # URL (PDF link)
            ])

    df = pd.DataFrame(data, columns=[
        'Issue No', 'Issue Date', 'Gazette Number', 'Category',
        'Subject', 'Department', 'G.O No', 'URL'
    ])
    df['Issue Date'] = pd.to_datetime(df['Issue Date'], format='%d-%m-%Y')
    return df


def extract_gazatte_issue_dataframes(year):
    """
    Scrapes the ordinary gazette issue listing from the new site.

    New URL pattern: gazette.php?id={base64_year}
    Each issue row links to gazette_list_details.php?id={b64_issue}&date={b64_date}

    Parameters:
        year (int): The year to scrape.

    Returns:
        pandas.DataFrame: Columns: Issue No, Issue No and Date, Date, URL
    """
    b64_year = base64.b64encode(str(year).encode()).decode()
    url = f"https://www.stationeryprinting.tn.gov.in/gazette.php?id={b64_year}"
    print(f'  Fetching ordinary gazette issues for {year}...')
    response = requests.get(url, timeout=30)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table')
    if not table:
        print(f'  No table found for {year}')
        return pd.DataFrame()

    data = []
    for row in table.find_all('tr')[1:]:
        cells = row.find_all('td')
        if len(cells) >= 2:
            link = cells[0].find('a')
            if link:
                href = link.get('href', '')
                if href and not href.startswith('http'):
                    href = 'https://www.stationeryprinting.tn.gov.in/' + href.lstrip('/')
                full_text = cells[0].get_text(strip=True)
                parts = full_text.split('dated:')
                issue_no = parts[0].strip() if parts else ''
                date_str = parts[1].strip() if len(parts) > 1 else ''
                date_parsed = pd.to_datetime(date_str, format='%d-%m-%Y') if date_str else pd.NaT
                data.append([issue_no, full_text, date_parsed, href])

    df = pd.DataFrame(data, columns=['Issue No', 'Issue No and Date', 'Date', 'URL'])
    return df


def extract_gazette_dataframe(url):
    """
    Scrapes an individual ordinary gazette issue page from the new site.

    The page contains a table with PDF links in column 0 and content in column 1.
    PDF hrefs use backslash path separators which must be normalized.

    Parameters:
        url (str): Full URL to the gazette_list_details.php page.

    Returns:
        pandas.DataFrame: Columns: Part, Content, URL
    """
    print(f'    Fetching issue details...')
    response = requests.get(url, timeout=30)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table')
    if not table:
        print(f'    No table found')
        return pd.DataFrame()

    data = []
    for row in table.find_all('tr')[1:]:
        cells = row.find_all('td')
        if len(cells) >= 2:
            link = cells[0].find('a')
            pdf_link = link.get('href', '') if link else ''
            if pdf_link:
                pdf_link = pdf_link.replace('\\', '/')
                if not pdf_link.startswith('http'):
                    pdf_link = 'https://www.stationeryprinting.tn.gov.in/' + pdf_link.lstrip('/')
            part_text = cells[0].get_text(strip=True)
            content = cells[1].get_text(strip=True)
            data.append([part_text, content, pdf_link])

    df = pd.DataFrame(data, columns=['Part', 'Content', 'URL'])
    return df


def is_url_deleted(url):
    """Check if a PDF URL is no longer accessible (returns True for 404/deleted)."""
    s = requests.Session()
    a = requests.adapters.HTTPAdapter(max_retries=3)
    b = requests.adapters.HTTPAdapter(max_retries=3)
    s.mount('http://', a)
    s.mount('https://', b)
    try:
        r = s.get(url, stream=True, timeout=30)
        return r.status_code != 200
    except Exception:
        return True


def main(archive_mode):

    extraordinary_dataframes = []
    gazette_dataframes = []
    gazatte_issues_dataframes = []
    years = []

    if archive_mode == ArchiveMode.CURRENT_YEAR:
        years = [datetime.today().year]
    else:
        years = list(range(2008, 2027))

    for year in years:
        print(f'\n--- {year} ---')

        # Extraordinary gazettes (new website pattern)
        edf = extract_extraordinary_gazette(year)
        if not edf.empty:
            extraordinary_dataframes.append(edf)

        # Ordinary gazettes (new website pattern)
        try:
            issue_dataframe = extract_gazatte_issue_dataframes(year)
            if issue_dataframe.empty:
                continue
            gazatte_issues_dataframes.append(issue_dataframe)
            for idx, series in issue_dataframe.iterrows():
                gazette_dataframe = extract_gazette_dataframe(series['URL'])
                gazette_dataframe['Date'] = series['Date']
                gazette_dataframe['Issue'] = series['Issue No']
                gazette_dataframes.append(gazette_dataframe)
        except Exception as e:
            print(f'  Warning: Ordinary gazette scrape failed for {year}: {e}')

    if not extraordinary_dataframes:
        print('No extraordinary gazette data scraped. Exiting.')
        return

    extraordinary_dataframes = pd.concat(
        extraordinary_dataframes, ignore_index=True)

    extraordinary_dataframes['Deleted'] = extraordinary_dataframes.apply(
        lambda row: is_url_deleted(row.URL), axis=1)

    print('Archiving extraordinary gazettes to Wayback Machine...')
    extraordinary_dataframes = wayback_archival(
        extraordinary_dataframes, url_col="URL")

    if gazatte_issues_dataframes:
        gazatte_issues_dataframes = pd.concat(
            gazatte_issues_dataframes, ignore_index=True)
    if gazette_dataframes:
        gazette_dataframes = pd.concat(gazette_dataframes, ignore_index=True)
        gazette_dataframes = gazette_dataframes.sort_values(
            by='Date', ascending=False)
        gazette_dataframes['Deleted'] = gazette_dataframes.apply(
            lambda row: is_url_deleted(row.URL), axis=1)
        print('Archiving ordinary gazettes to Wayback Machine...')
        gazette_dataframes = wayback_archival(
            gazette_dataframes, url_col="URL")

    if archive_mode == ArchiveMode.CURRENT_YEAR:
        ys = str(datetime.today().year)
        extraordinary_dataframes.to_csv(
            f'data/ExtraOrdinaryGazattes_{ys}.csv', index=False)
        extraordinary_dataframes.to_parquet(
            f'data/ExtraOrdinaryGazattes_{ys}.parquet', index=False, engine='pyarrow')
        if gazatte_issues_dataframes:
            gazatte_issues_dataframes.to_csv(
                f'data/GazatteIssues_{ys}.csv', index=False)
            gazatte_issues_dataframes.to_parquet(
                f'data/GazatteIssues_{ys}.parquet', index=False, engine='pyarrow')
        if gazette_dataframes:
            gazette_dataframes.to_csv(
                f'data/Gazattes_{ys}.csv', index=False)
            gazette_dataframes.to_parquet(
                f'data/Gazattes_{ys}.parquet', index=False, engine='pyarrow')
    else:
        extraordinary_dataframes.to_csv(
            'data/ExtraOrdinaryGazattes.csv', index=False)
        extraordinary_dataframes.to_parquet(
            'data/ExtraOrdinaryGazattes.parquet', index=False, engine='pyarrow')
        if gazatte_issues_dataframes:
            gazatte_issues_dataframes.to_csv(
                'data/GazatteIssues.csv', index=False)
            gazatte_issues_dataframes.to_parquet(
                'data/GazatteIssues.parquet', index=False, engine='pyarrow')
        if gazette_dataframes:
            gazette_dataframes.to_csv(
                'data/Gazattes.csv', index=False)
            gazette_dataframes.to_parquet(
                'data/Gazattes.parquet', index=False, engine='pyarrow')


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
