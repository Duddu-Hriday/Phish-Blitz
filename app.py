from flask import Flask, render_template, request, flash,redirect,url_for
import time
from concurrent.futures import ThreadPoolExecutor
from phish_tank_scraper import fetch_and_scrape_page
from url_features_extraction import extract_features
from html_features_extraction import main_fun
from download_webpage import clean_url,update_html,url_screenshot,compare_images,move_to_partially_downloaded
from phishstats import fetch_phishing_data
import os
import csv
import logging
import shutil
import tldextract
import subprocess
import threading
import random
import time
import requests

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
# def phishing_urls():
#     user_input = request.form['userInput']
#     global phishing_data
#     day = 0
#     pages = int(user_input)

#     with ThreadPoolExecutor(max_workers=100) as executor:
#         futures = [executor.submit(fetch_and_scrape_page, day, page, phishing_data) for page in range(pages)]

#         # Ensure all threads have completed
#         for future in futures:
#             try:
#                 future.result()
#             except Exception as e:
#                 print(f"Thread resulted in an error: {e}")

#     print(phishing_data)

#     # Do something with user_input, such as processing or storing it
#     return render_template("phishing-urls.html",urls = phishing_data)
def phishing_urls():
    user_input = request.form['userInput']
    global phishing_data
    count = int(user_input)
    phishing_data = fetch_phishing_data(count)
    return render_template("phishing-urls.html", urls = phishing_data)


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


@app.route('/download-legitimate-sites')
def download_legitimate_sites():
    global legitimate_urls_dict
    

    base_dir = 'legitimate_resources'
    resources_base_dir = os.path.join(base_dir, 'fully_downloaded_web_pages')
    partially_downloaded_base_dir = os.path.join(base_dir, 'no_screenshot_web_pages')
    os.makedirs(resources_base_dir, exist_ok=True)
    os.makedirs(partially_downloaded_base_dir, exist_ok=True)

    csv_file = os.path.join(base_dir,"info.csv")
    if os.path.exists(csv_file):
        print("csv file already exists")
    else:
        print("creating csv file")
        headers = ['Index', 'URL', 'HTML Folder']
        with open(csv_file, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            # Writing the header
            csvwriter.writerow(headers)

    count = 0

    for url_dict in legitimate_urls_dict:

        count += 1
        try:
            start_time = time.time()
            if not (url_dict['url'].startswith('https://') or url_dict['url'].startswith('http://')):
                url = "http://" + url_dict['url']
            else:
                url = url_dict['url']

            new_cleaned_url = clean_url(url)
            if new_cleaned_url.startswith('http://'):
                cleaned_url = new_cleaned_url[7:]
            else:
                cleaned_url = new_cleaned_url[8:]

            url_parts = cleaned_url.split('/')

            if len(url_parts) == 1:
                # Case 1: URL is of the form google.com
                folder = cleaned_url
                html_file = "index.html"  # Default to index.html
            elif len(url_parts) > 1:
                if url_parts[-1] == '':
                    # Case 3: URL is of the form google.com/images/
                    folder = cleaned_url.rstrip('/')
                    html_file = "index.html"  # Default to index.html
                else:
                    # Case 2: URL is of the form google.com/images
                    folder = '/'.join(url_parts[:-1])
                    html_file = url_parts[-1] + ".html"

            print(f"Folder Path: {folder}")
            print(f"HTML File: {html_file}")

                
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
            # try:
            #     response = requests.get(new_cleaned_url, headers={'User-Agent': user_agent}, timeout=10)
            #     status_code = response.status_code
            # except requests.exceptions.RequestException as e:
            #     # Handle any requests exceptions, such as timeouts, connection errors, etc.
            #     status_code = "Request Failed"

            # with open("requests_check_legit.txt", "a") as f:
            #     f.write(f"{new_cleaned_url},{status_code},{result.returncode}\n")

            logging.info(result)
            full_folder = os.path.join(outer_folder, folder)
            # if not os.path.isdir(full_folder):
            #         parent_folder = os.path.dirname(full_folder)
            #         if os.path.exists(parent_folder) and os.path.isdir(parent_folder):
            #             print(f"'{full_folder}' is not a directory. Checking parent folder '{parent_folder}'.")
            #             full_folder = parent_folder
            #         else:
            #             print(f"Neither '{full_folder}' nor its parent folder exists.")
            #             move_to_partially_downloaded(full_folder, partially_downloaded_base_dir)
            #             return
                    
            is_index = False
            for filename in os.listdir(full_folder):
                if os.path.isfile(os.path.join(full_folder, filename)):
                    if filename == "index.html":
                        index_html = 'index.html'
                        is_index = True
                        break
            if not is_index and html_file!='index.html':
                for filename in os.listdir(full_folder):
                    if os.path.isfile(os.path.join(full_folder, filename)):
                        if filename == html_file:
                            index_html = html_file
                            is_index = True
                            break
            if not is_index:
                for filename in os.listdir(full_folder):
                    if os.path.isfile(os.path.join(full_folder, filename)) and filename.endswith('html'):
                        index_html = filename
                        is_index = True
                        break

            # if not is_index:
            #     # If not found in the expected folder, check one level up
            #     parent_folder = os.path.dirname(full_folder)
            #     print(f"index.html not found in {full_folder}, checking in parent folder {parent_folder}")
            #     # Check if parent_folder exists and search there
            #     if os.path.exists(parent_folder):
            #         for filename in os.listdir(parent_folder):
            #             if os.path.isfile(os.path.join(parent_folder, filename)) and filename.endswith('html'):
            #                 index_html = filename
            #                 full_folder = parent_folder  # Update to the parent folder
            #                 is_index = True
            #                 break
                            
            # If still not found, move the folder to partially downloaded and continue
            if not is_index:
                print("index.html not found in parent folder either")
                move_to_partially_downloaded(outer_folder, partially_downloaded_base_dir)
                continue
                    
            print("HTML FILE = " + index_html)

            html_file = os.path.join(outer_folder, folder, index_html)
            resource_dir = os.path.join(outer_folder, folder, 'local_resources')

            update_html(html_file, resource_dir, new_cleaned_url)
            # d_time = time.time()

            screenshots = os.path.join(resource_dir, 'screenshots')
            os.makedirs(screenshots, exist_ok=True)
            online = os.path.join(screenshots, 'online.png')
            offline = os.path.join(screenshots, 'offline.png')

            path_wanted = "file://" + os.path.abspath(html_file)
            print("absolute path = " + path_wanted)
            ss_start = time.time()
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
            ss_end = time.time()
            # screenshots_taken = True
            # ssim_index = "Null"
            # hist_corr = "Null"
            screenshots_taken = True
            if not os.path.exists(online) and not os.path.exists(offline):
                screenshots_taken = False
                logging.warning(f"One of {online} or {offline} is missing. Deleting {outer_folder}...")
                # count -= 1
                move_to_partially_downloaded(outer_folder, partially_downloaded_base_dir)

            if os.path.exists(online) and os.path.exists(offline):
                ssim_index, hist_corr = compare_images(online, offline)

                print(f"SSIM Index: {ssim_index}")
                print(f"Histogram Correlation: {hist_corr}")
                image = os.path.join(base_dir,'image_comparision.txt')
                print(f"{str(cleaned_url)}\tSSIM Index = {str(ssim_index)}\tHistogram Correlation = {str(hist_corr)}\n")
                with open(image, 'a') as file:
                    file.write(f"{str(cleaned_url)}\tSSIM Index = {str(ssim_index)}\tHistogram Correlation = {str(hist_corr)}\n")
            # if hist_corr < 0.8:
            #     logging.warning(f"Histogram correlation {hist_corr} is less than 0.8. Deleting {outer_folder}...")
            #     count -= 1
            #     move_to_partially_downloaded(outer_folder, partially_downloaded_base_dir)
            end_time = time.time()
            total_time = end_time - start_time
            ss_time = ss_end - ss_start
            print(str(total_time)+","+str(ss_time)+","+str(screenshots_taken))
            with open("legitimate_observations.txt",'a') as obs_file:
                obs_file.write(str(total_time)+","+str(ss_time)+","+str(screenshots_taken)+"\n")
            # image = os.path.join(base_dir,'image_comparision.txt')
            # print(f"{str(cleaned_url)}\tSSIM Index = {str(ssim_index)}\tHistogram Correlation = {str(hist_corr)}\n")
            # with open(image, 'a') as file:
            #     file.write(f"{str(cleaned_url)}\tSSIM Index = {str(ssim_index)}\tHistogram Correlation = {str(hist_corr)}\n")

            info_arr = [str(count), str(cleaned_url), str(html_file)]
            print(info_arr)
            with open(csv_file, 'a', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(info_arr)

        except Exception as e:
            logging.error(f"An error occurred with URL {url_dict['url']}: {e}")
            continue   
    
    flash('Download complete!', 'success')
    return render_template('download-legitimate-intermediate.html')

@app.route('/download-phishing-sites')
def download_phishing_sites():
    global phishing_data
    
    base_dir = 'phishing_resources'
    resources_base_dir = os.path.join(base_dir, 'fully_downloaded_web_pages')
    partially_downloaded_base_dir = os.path.join(base_dir, 'no_screenshot_web_pages')
    os.makedirs(resources_base_dir, exist_ok=True)
    os.makedirs(partially_downloaded_base_dir, exist_ok=True)

    csv_file = os.path.join(base_dir,"info.csv")
    if os.path.exists(csv_file):
        print("csv file already exists")
    else:
        print("creating csv file")
        headers = ['Index', 'URL', 'HTML Folder']
        with open(csv_file, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            # Writing the header
            csvwriter.writerow(headers)
    count = 0

    for url_dict in phishing_data:

        count += 1
        try:
            start_time = time.time()
            if not (url_dict['url'].startswith('https://') or url_dict['url'].startswith('http://')):
                url = "http://" + url_dict['url']
            else:
                url = url_dict['url']
            
            new_cleaned_url = clean_url(url)
            if new_cleaned_url.startswith('http://'):
                cleaned_url = new_cleaned_url[7:]
            else:
                cleaned_url = new_cleaned_url[8:]
            
            url_parts = cleaned_url.split('/')
            
            if len(url_parts) == 1:
                # Case 1: URL is of the form google.com
                folder = cleaned_url
                html_file = "index.html"  # Default to index.html
            elif len(url_parts) > 1:
                if url_parts[-1] == '':
                    # Case 3: URL is of the form google.com/images/
                    folder = cleaned_url.rstrip('/')
                    html_file = "index.html"  # Default to index.html
                else:
                    # Case 2: URL is of the form google.com/images
                    folder = '/'.join(url_parts[:-1])
                    if html_file.endswith('.html'):
                        html_file = url_parts[-1]
                    else:
                        html_file = url_parts[-1] + ".html"
            
            print(f"Folder Path: {folder}")
            print(f"HTML File: {html_file}")

            domain = tldextract.extract(cleaned_url).domain
            outer_folder = os.path.join(resources_base_dir, f"{count}_{domain}")
            print(cleaned_url)

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

            # try:
            #     response = requests.get(new_cleaned_url, headers={'User-Agent': user_agent}, timeout=10)
            #     status_code = response.status_code
            # except requests.exceptions.RequestException as e:
            #     # Handle any requests exceptions, such as timeouts, connection errors, etc.
            #     status_code = "Request Failed"

            # # Log the URL, status code, and wget return code to why.txt
            # with open("requests_check_phishing.txt", "a") as f:
            #     f.write(f"{new_cleaned_url},{status_code},{result.returncode}\n")

            logging.info(result)
            full_folder = os.path.join(outer_folder, folder)

            # if not os.path.isdir(full_folder):
            #     parent_folder = os.path.dirname(full_folder)
            #     if os.path.exists(parent_folder) and os.path.isdir(parent_folder):
            #         print(f"'{full_folder}' is not a directory. Checking parent folder '{parent_folder}'.")
            #         full_folder = parent_folder
            #     else:
            #         print(f"Neither '{full_folder}' nor its parent folder exists.")
            #         move_to_partially_downloaded(full_folder, partially_downloaded_base_dir)
            #         continue

            is_index = False
            for filename in os.listdir(full_folder):
                if os.path.isfile(os.path.join(full_folder, filename)):
                    if filename == "index.html":
                        index_html = 'index.html'
                        is_index = True
                        break
            if not is_index and html_file!='index.html':
                for filename in os.listdir(full_folder):
                    if os.path.isfile(os.path.join(full_folder, filename)):
                        if filename == html_file:
                            index_html = html_file
                            is_index = True
                            break
                    
            if not is_index:
                for filename in os.listdir(full_folder):
                    if os.path.isfile(os.path.join(full_folder, filename)) and filename.endswith('html'):
                        index_html = filename
                        is_index = True
                        break
                # else:
                #     # If not found in the expected folder, check one level up
                #     parent_folder = os.path.dirname(full_folder)
                #     print(f"index.html not found in {full_folder}, checking in parent folder {parent_folder}")

                #     # Check if parent_folder exists and search there
                #     if os.path.exists(parent_folder):
                #         for filename in os.listdir(parent_folder):
                #             if os.path.isfile(os.path.join(parent_folder, filename)) and filename.endswith('html'):
                #                 index_html = filename
                #                 full_folder = parent_folder  # Update to the parent folder
                #                 is_index = True
                #                 break
                            
                    # If still not found, move the folder to partially downloaded and continue
            if not is_index:
                print("index.html not found in parent folder either")
                move_to_partially_downloaded(outer_folder, partially_downloaded_base_dir)
                continue
                    
            print("HTML FILE = " + index_html)

            html_file = os.path.join(outer_folder, folder, index_html)
            resource_dir = os.path.join(outer_folder, folder, 'local_resources')

            update_html(html_file, resource_dir, new_cleaned_url)
            screenshots = os.path.join(resource_dir, 'screenshots')
            os.makedirs(screenshots, exist_ok=True)
            online = os.path.join(screenshots, 'online.png')
            offline = os.path.join(screenshots, 'offline.png')

            path_wanted = "file://" + os.path.abspath(html_file)
            print("absolute path = " + path_wanted)
            ss_start = time.time()
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
            ss_end = time.time()
            screenshots_taken = True
            if not os.path.exists(online) and not os.path.exists(offline):
                screenshots_taken =  False
                logging.warning(f" {online} and {offline} images are missing. Deleting {outer_folder}...")
                # count -= 1
                move_to_partially_downloaded(outer_folder, partially_downloaded_base_dir)

            if os.path.exists(online) and os.path.exists(offline):
                ssim_index, hist_corr = compare_images(online, offline)
                print(f"SSIM Index: {ssim_index}")
                print(f"Histogram Correlation: {hist_corr}")
                with open('image_comparision.txt', 'a') as file:
                    file.write(f"{str(cleaned_url)}\tSSIM Index = {str(ssim_index)}\tHistogram Correlation = {str(hist_corr)}\n")
            # if hist_corr < 0.8:
            #     logging.warning(f"Histogram correlation {hist_corr} is less than 0.8. Deleting {outer_folder}...")
            #     count -= 1
            #     move_to_partially_downloaded(outer_folder, partially_downloaded_base_dir)
            end_time = time.time()
            total_time = end_time - start_time
            ss_time = ss_end - ss_start
            with open("phishing_observations.txt","a") as obs_file:
                obs_file.write(str(total_time)+","+str(ss_time)+","+str(screenshots_taken)+"\n")
            

            info_arr = [str(count), str(cleaned_url), str(html_file)]
            with open(csv_file, 'a', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(info_arr)

        except Exception as e:
            logging.error(f"An error occurred with URL {url_dict['url']}: {e}")
            continue   
    
    flash('Download complete!', 'success')
    return render_template('download-phishing-intermediate.html')

@app.route('/collected-phishing-urls')
def collected_phishing_urls():
    return render_template('collected-phishing-urls.html')

@app.route('/choice')
def choice():
    return render_template('choice-urls.html')

@app.route('/upload', methods=['POST'])
def upload():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        global legitimate_urls
        global legitimate_urls_dict
        file_lines = uploaded_file.readlines()
        file_lines_utf8 = [line.decode('utf-8').strip() for line in file_lines]
        urls_dict = [{"url": url.decode('utf-8').strip()} for url in file_lines]
        
        # print(type(urls_dict))
        legitimate_urls = file_lines_utf8
        legitimate_urls_dict =urls_dict
        return render_template('legitimate-urls.html',urls = legitimate_urls,count = len(file_lines))
    else:
        return 'file Not Uploaded'
    
@app.route('/phishing-html-features')
def phishing_html_features():
    features = main_fun('phishing_resources')
    return render_template('phishing-html-features.html', features = features)


@app.route('/legitimate-html-features')
def legitimate_html_features():
    features = main_fun('legitimate_resources')
    print(features)
    return render_template('legitimate-html-features.html',features = features)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
