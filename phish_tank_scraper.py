import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urlsplit, urlunsplit
from datetime import datetime
import re
import time
from concurrent.futures import ThreadPoolExecutor
import csv




def html_file(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Non 200 Status code: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None

def extract_time(input_string):
    pattern = r"(\w+ \d{1,2}[a-z]{2} \d{4} \d{1,2}:\d{2} [APM]{2})"
    match = re.search(pattern, input_string)

    date_str = match.group(1)

    # Remove the ordinal suffix (st, nd, rd, th) from the day
    date_str = re.sub(r'(\d{1,2})[a-z]{2}', r'\1', date_str)

    # Parse the date string into a datetime object
    date_time_obj = datetime.strptime(date_str, "%b %d %Y %I:%M %p")

    # Use the extracted date and time for future usage
    formatted_date_time = date_time_obj.strftime("%Y-%m-%d %H:%M:%S")
    # print("Formatted Date and Time:", formatted_date_time)
    return formatted_date_time

def remove_last_part_of_url(url):
    if not (str(url).startswith('https://') or str(url).startswith('http://')):
        url = 'https://' + url

    suffix = '...added'
    if url.endswith(suffix):
        return url[:-len(suffix)]
    if url.endswith('added'):
        return url[:-len('added')]
    return url

def scraping(html_content, data):
    if not html_content:
        print("No HTML content to scrape")
        return

    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table')
    if not table:
        print("No table found in HTML content")
        return

    count = 0
    urls = []
    valid_phish = []
    online = []
    time_list = []
    for tr in table.find_all('tr'):
        if count == 0:
            count = 1
            continue
        td = tr.find_all('td')
        span = td[1].find_all('span')
        formatted_time = extract_time(span[0].text)
        time_list.append(formatted_time)
        url = td[1].get_text(strip=True).split()[0]
        new_url = remove_last_part_of_url(url)
        urls.append(new_url)
        valid_phish.append(td[3])
        online.append(td[4])

    for i in range(len(urls)):
        
        data.append({
            "url": urls[i],
            "valid_phish": valid_phish[i].text,
            "online": online[i].text,
            "time": time_list[i]
        })



def fetch_and_scrape_page(day, page, data):
    url = f"https://phishtank.org/phish_search.php?page={page}&valid=y&Search=Search"
    html_content = html_file(url)
    scraping(html_content, data)
    time.sleep(1)

