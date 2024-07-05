'''
    Code written by Duddu Hriday, 4th Year student at IIT Dharwad
    This code is a part of a project on Phishing website detection with Professor Tamal Das and Aditya Kulkarni
    This code does the following things:
    - Download webpage using wget
    - Download required resources like css, js, images, other files using requests Library
    - Change the path pointed to the server in the html file to the local path to load them even when offline
'''
##----Threading Included
##-----All resources download

import os
import requests
import hashlib
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import chardet
import time
from requests.exceptions import SSLError, ConnectionError, Timeout
import logging
from selenium import webdriver

import time

import cv2
from skimage.metrics import structural_similarity as ssim

import threading

from selenium.common.exceptions import TimeoutException

import shutil
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# def modify_url(url):
#     if url.endswith('/'):
#         return url
#     else:
#         parts = url.split('/')
#         # Remove the last part
#         parts.pop()
#         # Reconstruct the URL
#         modified_url = '/'.join(parts)
#         return modified_url
  
# Helper functions
def is_valid_url(url):
    parsed_url = urlparse(url)
    return parsed_url.scheme in ('http', 'https') and not url.startswith('data:')

def sanitize_filename(url, ext, max_length=255):
    parsed_url = urlparse(url)
    url_hash = hashlib.md5(url.encode()).hexdigest()
    if ext == 'css':
        extension = '.css'
    elif ext == 'js':
        extension = '.js'

    elif ext == 'html':
        extension = os.path.splitext(parsed_url.path)[1]
        if not extension:
            extension = '.html'
    elif ext == 'img':
        extension = os.path.splitext(parsed_url.path)[1]
        if not extension:
            extension = '.png'
    else:
        extension = os.path.splitext(parsed_url.path)[1]
    filename = f"{url_hash}{extension}"
    print("url = "+str(parsed_url))
    print("filename = "+filename)
    return filename[:max_length]

def download_resource(url, save_dir, filename, retries=3, delay=5):
    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, filename)
    attempt = 0
    while attempt < retries:
        try:
            with requests.Session() as session:
                session.verify = False  # Disable SSL verification
                response = session.get(url, stream=True, timeout=10)
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                response.close()
            logging.info(f"Successfully downloaded {url} to {filepath}")
            break  # Exit the loop if the download is successful
        except (SSLError, ConnectionError, Timeout) as e:
            attempt += 1
            if attempt >= retries:
                logging.error(f"Failed to download {url} after {retries} attempts. Error: {e}")
            else:
                logging.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
        finally:
            if 'response' in locals() and response is not None:
                response.close()

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
    result = chardet.detect(raw_data)
    return result['encoding']

def read_file_with_fallbacks(file_path):
    encodings = [detect_encoding(file_path), 'utf-8', 'latin-1']
    for encoding in encodings:
        if encoding is None:
            continue
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, TypeError):
            continue
    raise UnicodeDecodeError(f"Unable to decode file {file_path} with available encodings.")


def update_html(html_file, resource_dir, new_cleaned_url):
    print(f"Updating HTML file: {html_file}")
    if not os.path.isfile(html_file):
        print(f"File not found: {html_file}")
        return

    try:
        html_content = read_file_with_fallbacks(html_file)
    except UnicodeDecodeError as e:
        print(e)
        return

    print("Parsing HTML content...")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    def process_attributes():
        print("Processing all attributes for all tags...")
        for tag in soup.find_all():
            for attr, value in tag.attrs.items():
                if tag.name in ['img', 'script', 'link', 'iframe'] and attr in ['src', 'href']:
                    if isinstance(value, str):
                        if value.startswith('http') or value.startswith('https'):
                            continue
                        elif value.startswith('/'):
                            tag[attr] = urljoin(new_cleaned_url, value)
                        else:
                            tag[attr] = new_cleaned_url + '/' + value
                else:
                    if isinstance(value, str) and value.startswith('/'):
                        tag[attr] = urljoin(new_cleaned_url, value)

    def remove_base_tag():
        nonlocal soup
        base_tag = soup.find('base')
        if base_tag:
            print("Removing base tag...")
            base_tag.decompose()

    def process_link_tag(tag):
        href = tag.get('href')

        if tag.name == 'link':
            if tag.get('rel') == ['stylesheet'] or tag.get('as') == 'style':
                if href and is_valid_url(href):
                    css_url = urljoin(html_file, href)
                    css_filename = sanitize_filename(href, 'css')  # First call to sanitize_filename
                    local_path = os.path.join('local_resources', 'css', css_filename)
                    tag['href'] = local_path
                    download_resource(css_url, os.path.join(resource_dir, 'css'), css_filename)
            elif tag.get('rel') == ['manifest']:
                if href and is_valid_url(href):
                    manifest_url = urljoin(html_file, href)
                    manifest_filename = sanitize_filename(href, 'css')
                    tag['href'] = os.path.join('local_resources', 'css', manifest_filename)
                    download_resource(manifest_url, os.path.join(resource_dir, 'css'), manifest_filename)
            elif tag.get('rel') == ['icon']:
                if href and is_valid_url(href):
                    icon_url = urljoin(html_file, href)
                    icon_filename = sanitize_filename(href, 'img')
                    local_path = os.path.join('local_resources', 'img', icon_filename)
                    tag['href'] = local_path
                    download_resource(icon_url, os.path.join(resource_dir, 'img'), icon_filename)

            elif tag.get('as') =='script':
                    if href and is_valid_url(href):
                        icon_url = urljoin(html_file, href)
                        icon_filename = sanitize_filename(href, 'js')
                        local_path = os.path.join('local_resources', 'js', icon_filename)
                        tag['href'] = local_path
                        download_resource(icon_url, os.path.join(resource_dir, 'js'), icon_filename)

    def process_script_tag(tag):
        src = tag.get('src')
        if src and is_valid_url(src):
            js_url = urljoin(html_file, src)
            js_filename = sanitize_filename(src, 'js')
            local_path = os.path.join('local_resources', 'js', js_filename)
            tag['src'] = local_path
            download_resource(js_url, os.path.join(resource_dir, 'js'), js_filename)

    def process_iframe_tag(tag):
        src = tag.get('src')
        if src and is_valid_url(src):
            iframe_url = urljoin(html_file, src)
            iframe_filename = sanitize_filename(src, ' ')
            local_path = os.path.join('local_resources', 'iframes', iframe_filename)
            tag['src'] = local_path
            download_resource(iframe_url, os.path.join(resource_dir, 'iframes'), iframe_filename)

    def process_img_tag(tag):
        src = tag.get('src')
        if src and is_valid_url(src):
            img_url = urljoin(html_file, src)
            img_filename = sanitize_filename(src, 'img')
            local_path = os.path.join('local_resources', 'img', img_filename)
            tag['src'] = local_path
            download_resource(img_url, os.path.join(resource_dir, 'img'), img_filename)
        data_src = tag.get('data-src')
        if data_src and is_valid_url(data_src):
            data_img_url = urljoin(html_file, data_src)
            data_img_filename = sanitize_filename(data_src, 'img')
            local_path = os.path.join('local_resources', 'img', data_img_filename)
            tag['data-src'] = local_path
            tag['src'] = local_path
            download_resource(data_img_url, os.path.join(resource_dir, 'img'), data_img_filename)
        if tag.has_attr('srcset'):
            del tag['srcset']


    def process_remaining_tags():
        print(f"Processing other tags...")

        for meta_tag in soup.find_all('meta', attrs={'http-equiv': 'refresh'}):
            meta_tag.decompose()
        for tag in soup.find_all():
            # Check if tag is one of the specified tags
            if tag.name in ['a', 'script', 'link', 'iframe', 'img', 'meta', 'form']:
                continue
            
            # Check all attributes of the tag for URLs
            for attr, value in list(tag.attrs.items()):
                if isinstance(value, str) and value.startswith(('http', 'https')):
                    # Unwrap the link
                    tag.unwrap()
                    break

    def remove_source_tags():
        print("Removing source tags")
        for s in soup.select('source'):
            s.extract()

    def remove_noscript_tags():
        print("Removing noscript tags...")
        for tag in soup.find_all('noscript'):
            tag.unwrap()

    process_attributes()
    remove_base_tag()

    # Create and start a thread for each link tag
    link_tags = soup.find_all('link')
    print(f"Starting threads for {len(link_tags)} link tags...")
    link_threads = [threading.Thread(target=process_link_tag, args=(tag,)) for tag in link_tags]
    for thread in link_threads:
        thread.start()

    # Create and start a thread for each script tag
    script_tags = soup.find_all('script')
    print(f"Starting threads for {len(script_tags)} script tags...")
    script_threads = [threading.Thread(target=process_script_tag, args=(tag,)) for tag in script_tags]
    for thread in script_threads:
        thread.start()

    # Create and start a thread for each iframe tag
    iframe_tags = soup.find_all('iframe')
    print(f"Starting threads for {len(iframe_tags)} iframe tags...")
    iframe_threads = [threading.Thread(target=process_iframe_tag, args=(tag,)) for tag in iframe_tags]
    for thread in iframe_threads:
        thread.start()

    # Create and start a thread for each img tag
    img_tags = soup.find_all('img')
    print(f"Starting threads for {len(img_tags)} img tags...")
    img_threads = [threading.Thread(target=process_img_tag, args=(tag,)) for tag in img_tags]
    for thread in img_threads:
        thread.start()

    print("Starting threads for removing noscript tags...")
    noscript_thread = threading.Thread(target=remove_noscript_tags)
    noscript_thread.start()

    print("Starting threads for removing source tags...")
    source_thread = threading.Thread(target=remove_source_tags)
    source_thread.start()

    # Wait for all threads to complete
    all_threads = link_threads + script_threads + iframe_threads + img_threads + [noscript_thread, source_thread]
    print("Waiting for all threads to complete...")
    for thread in all_threads:
        thread.join()

    process_remaining_tags()

    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print("Update completed.")

def clean_url(url):

    parsed_url = urlparse(url)
    
    # Remove :443 if it is present in the netloc
    netloc = parsed_url.netloc
    if netloc.endswith(':443'):
        netloc = netloc[:-4]  # Remove the :443 part
    
    # Reconstruct the URL with only the path component
    cleaned_url = urlunparse((parsed_url.scheme, netloc, parsed_url.path, '', '', ''))
    
    return cleaned_url



def url_screenshot(url, filename):
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('--window-size=1920,1080')  # Set a larger window size
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.set_page_load_timeout(15)
        
        try:
            # Open the URL
            driver.get(url)
            
            # Allow some time for the page to load
            time.sleep(15)  # Wait for 10 seconds

        except TimeoutException:
            print(f"Page load timed out for {url}. Stopping further loading.")
            driver.execute_script("window.stop();")
        
        # Scroll to capture the full height of the webpage
        total_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1920, total_height)  # Set window size to capture the full height
        driver.execute_script("window.scrollTo(0, 0);")  # Scroll to the top of the page
        
        try:
            driver.save_screenshot(filename)
            print(f"Screenshot saved for {url} as {filename}")
        except Exception as e:
            print(f"An error occurred while capturing screenshot for {url}: {e}")

    finally:
        driver.quit()
    

def compare_images(image1, image2):
    # Read images
    img1 = cv2.imread(image1)
    img2 = cv2.imread(image2)

    # Resize images to the same dimensions
    width = min(img1.shape[1], img2.shape[1])
    height = min(img1.shape[0], img2.shape[0])
    img1 = cv2.resize(img1, (width, height))
    img2 = cv2.resize(img2, (width, height))

    # Convert images to grayscale
    gray_img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray_img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # Compute SSIM (Structural Similarity Index)
    ssim_index = ssim(gray_img1, gray_img2)

    # Compute histogram correlation
    hist_corr = cv2.compareHist(cv2.calcHist([gray_img1],[0],None,[256],[0,256]),
                                cv2.calcHist([gray_img2],[0],None,[256],[0,256]),
                                cv2.HISTCMP_CORREL)

    return ssim_index, hist_corr


def move_to_partially_downloaded(source_folder, destination_base_dir):
    destination_folder = os.path.join(destination_base_dir, os.path.basename(source_folder))
    shutil.move(source_folder, destination_folder)
    logging.info(f"Moved {source_folder} to {destination_folder}")

# Main part of the script

# print("-----------------------WEB RESOURCES DOWNLOADER---------------------------------")
# ch = input("Enter 1 to download legitimate sources and 2 for downloading phishing sources ")

# if ch == "1":
#     extract_legitimate_urls()

# elif ch == "2":
#     extract_phishing_urls()

# else:
#     print('Wrong choice..Exiting......')
#     exit




