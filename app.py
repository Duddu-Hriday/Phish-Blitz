from flask import Flask, render_template, request, flash,redirect,url_for
import time
from concurrent.futures import ThreadPoolExecutor
from phish_tank_scraper import fetch_and_scrape_page
from feature_extraction import extract_features
from download_webpage import clean_url,update_html,url_screenshot,compare_images,move_to_partially_downloaded
import os
import csv
import logging
import shutil
import tldextract
import subprocess
import threading
import random

app = Flask(__name__)
app.secret_key = "Hello Hriday"
phishing_data = []
legitimate_urls = []
legitimate_urls_dict = []
@app.route("/")
def home_page():
    return render_template('home.html')

@app.route("/fetch-urls")
def fetch_urls_page():
    return render_template("urls.html")

@app.route("/phishing-urls", methods=["POST"])
def phishing_urls():
    user_input = request.form['userInput']
    global phishing_data
    day = 0
    pages = int(user_input)

    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(fetch_and_scrape_page, day, page, phishing_data) for page in range(pages)]

        # Ensure all threads have completed
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"Thread resulted in an error: {e}")

    print(phishing_data)

    # Do something with user_input, such as processing or storing it
    return render_template("phishing-urls.html",urls = phishing_data)

@app.route("/legitimate-urls", methods = ["POST"])
def legitimate_urls():
    global legitimate_urls,legitimate_urls_dict
    user_input = int(request.form['userInputLegit'])

    with open('urls.txt', 'r') as file:
        legitimate_urls = file.readlines()
        
    legitimate_urls = legitimate_urls[:user_input]
    legitimate_urls_dict = [{"url": url.strip()} for url in legitimate_urls]
    # print(legitimate_urls_dict)
    
    return render_template('legitimate-urls.html',count = int(user_input),urls = legitimate_urls)

@app.route("/phishing-features")
def phishing_features():
    global phishing_data
    features = extract_features(phishing_data)
    return render_template('phishing-url-features.html',features = features)

@app.route("/legitimate-features")
def legitimate_features():
    global legitimate_urls_dict
    features = extract_features(legitimate_urls_dict)
    return render_template('legitimate-url-features.html',features = features)

@app.route("/download-legitimate")
def intermeditate_step():
    return render_template('download-legitimate.html')

@app.route('/download-legitimate-sites', methods=['GET', 'POST'])
def download_legitimate_sites():
    global legitimate_urls_dict
    download_path = request.form['folderPath'].replace('\\', '/')
    print(download_path)
    csv_file = "info.csv"
    if os.path.exists(csv_file):
        print("csv file already exists")
    else:
        print("creating csv file")
        headers = ['Index', 'URL', 'HTML Folder']
        with open(csv_file, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            # Writing the header
            csvwriter.writerow(headers)

    # resources_base_dir = 'legitimate_resources'
    resources_base_dir  = os.path.join(download_path,'legitimate_resources')
    partially_downloaded_base_dir = os.path.join(download_path,'partially_downloaded_web_pages')
    # os.makedirs(partially_downloaded_base_dir, exist_ok=True)
    count = 0

    for url_dict in legitimate_urls_dict:

        count += 1
        try:
            url = "https://" + url_dict['url']
            new_cleaned_url = clean_url(url)
            cleaned_url = new_cleaned_url[8:]
            folder = cleaned_url
            domain = tldextract.extract(cleaned_url).domain
            outer_folder = os.path.join(resources_base_dir, f"{count}_{domain}")
            print(cleaned_url + " -> " + folder)

            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
                # Add more user agents as needed
            ]
            user_agent = random.choice(user_agents)

            command = [
                'wget',
                '--mirror',
                '--convert-links',
                '--adjust-extension',
                '--page-requisites',
                '--no-parent',
                '-U',
                user_agent,
                '--timeout=10',
                '-o', 'log.txt',
                '-P', outer_folder,
                new_cleaned_url
            ]

            # Prefix the wget command with `timeout 30`
            full_command = ['timeout', '10'] + command

            result = subprocess.run(full_command, text=True, capture_output=True)

            logging.info(result)
            full_folder = os.path.join(outer_folder, folder)

            is_index = False
            for filename in os.listdir(full_folder):
                if os.path.isfile(os.path.join(full_folder, filename)):
                    if filename == "index.html":
                        index_html = 'index.html'
                        is_index = True
                        break

            if not is_index:
                for filename in os.listdir(full_folder):
                    if os.path.isfile(os.path.join(full_folder, filename)) and filename.endswith('html'):
                        index_html = filename
                        is_index = True
                        break
                else:
                    # count -= 1
                    move_to_partially_downloaded(outer_folder, partially_downloaded_base_dir)

            index_html = 'index.html'
            print("HTML FILE = " + index_html)

            html_file = os.path.join(outer_folder, folder, index_html)
            resource_dir = os.path.join(outer_folder, folder, 'local_resources')

            update_html(html_file, resource_dir, new_cleaned_url)
            d_time = time.time()

            screenshots = os.path.join(resource_dir, 'screenshots')
            os.makedirs(screenshots, exist_ok=True)
            online = os.path.join(screenshots, 'online.png')
            offline = os.path.join(screenshots, 'offline.png')

            path_wanted = "file://" + os.path.abspath(html_file)
            print("absolute path = " + path_wanted)

            images = [
                threading.Thread(target=url_screenshot, args=(new_cleaned_url, online)),
                threading.Thread(target=url_screenshot, args=(path_wanted, offline)),
            ]

            print("Starting image parallel tasks...")
            for task in images:
                task.start()

            print("Waiting for image tasks to complete...")
            for task in images:
                task.join()

            if not os.path.exists(online) or not os.path.exists(offline):
                logging.warning(f"One of {online} or {offline} is missing. Deleting {outer_folder}...")
                # count -= 1
                move_to_partially_downloaded(outer_folder, partially_downloaded_base_dir)

            ssim_index, hist_corr = compare_images(online, offline)

            print(f"SSIM Index: {ssim_index}")
            print(f"Histogram Correlation: {hist_corr}")
            if hist_corr < 0.9:
                logging.warning(f"Histogram correlation {hist_corr} is less than 0.9. Deleting {outer_folder}...")
                # count -= 1
                move_to_partially_downloaded(outer_folder, partially_downloaded_base_dir)

            with open('image_comparision.txt', 'a') as file:
                file.write(f"{cleaned_url}\tSSIM Index = {ssim_index}\tHistogram Correlation = {hist_corr}\n")

            info_arr = [count, cleaned_url, html_file]
            with open('info.csv', 'a', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(info_arr)

        except Exception as e:
            logging.error(f"An error occurred with URL {url_dict['url']}: {e}")
            continue   
    
    flash('Download complete!', 'success')
    return render_template('home.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
