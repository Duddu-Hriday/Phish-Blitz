'''
Functions written by Duddu Hriday:
- pre_at_urls
- is_link_valid
- multiple_https_check
- form_empty_action
- same_form_action_domain
- is_mail
- num_of_redirects
- has_window_status
- status_bar_customization
- https_in_domain
- abnormal_url
- is_at_symbol_present
- targeted_domain
'''
import os
import pandas as pd
from bs4 import BeautifulSoup, Comment
import tldextract
import numpy as np
from urllib.parse import urlparse
import csv

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import time
# Function to read HTML file content
def read_html_file(file_name):
    with open(file_name, 'r', encoding='utf-8') as file:
        content = file.read()
    return BeautifulSoup(content, 'html.parser')


## HTML - based feature extraction

class html_check():
    def __init__(self, text, url):  ##input the html and the domain name for example

        self.text = text
        self.url = url
        self.domain = tldextract.extract(self.url).domain

    # ------------------------------length of HTML----------------------------------------------

    def find_len(self, tag):
        if tag == '!--':
            soup = self.text
            len_sum = 0
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                len_sum += len(comment)
            return len_sum
        else:
            soup = self.text
            scripts = soup.find_all(str(tag))
            len_sum = 0

            for script in scripts:
                len_sum += len(script.text)
            return len_sum

    def len_html_tag(self):  ## this is the total length for 5 special tags
        return html_check.find_len(self, "style") + html_check.find_len(self, "link") + html_check.find_len(self,
                                                                                                            "form") + html_check.find_len(
            self, "!--") + html_check.find_len(self, "script")

    def len_html(self):
        return len(self.text.text)

    # ------------------------------hidden content------------------------------------------------------------------------
    def hidden_div(self):
        soup = self.text
        scripts = soup.find_all('div')
        find = 0
        for script in scripts:
            try:
                if str(script.attrs['style']) == 'visibility:hidden' or str(script.attrs['style']) == 'display:none':
                    find = 1
                    break
            except:
                continue
        return find

    def hidden_button(self):
        soup = self.text
        scripts = soup.find_all('button')
        find = 0
        for script in scripts:
            try:
                if str(script.attrs['disabled']) == 'disabled':
                    find = 1
                    break
            except:
                continue
        return find

    def hidden_input(self):
        soup = self.text
        scripts = soup.find_all('input')
        find = 0
        for script in scripts:
            try:
                if str(script.attrs['type']) == 'hidden' or str(script.attrs['disabled']) == 'disabled':
                    find = 1
                    break
            except:
                continue
        return find

    def hidden(self):  ## have hidden content
        return int(html_check.hidden_div(self) | html_check.hidden_button(self) | html_check.hidden_input(self))

    # ----------------------------link based------------------------------------------------

    def find_all_link(self):
        soup = self.text
        a_tags = soup.find_all('a')
        a_data = []

        for a_tag in a_tags:
            try:
                a_data.append(a_tag.attrs['href'])
            except:
                continue

        return a_data

    def find_source(self, tag):  ## find src attribute in <img> <link> ...
        if tag == 'link':
            soup = self.text
            links = soup.find_all('link')
            link_data = []

            for link in links:
                try:
                    link_data.append(link.attrs['href'])
                except:
                    continue
            return link_data

        else:
            soup = self.text
            resources = soup.find_all(str(tag))
            data = []

            for resource in resources:
                try:
                    data.append(resource.attrs['src'])
                except:
                    continue
            return data

    def internal_external_link(self):  ## Number of internal hyperlinks and number of external hyperlinks
        link_list = html_check.find_all_link(self)
        if len(link_list) == 0:  ## in case there is no hyperlink
            return [0, 0]

        count = 0
        for j in link_list:
            if "http" in j:
                brand = tldextract.extract(j).domain
                if str(brand) == self.domain:
                    count += 1
            else:
                count += 1

        return [count, len(link_list) - count]

    def empty_link(self):  ## Number of empty links
        link_list = html_check.find_all_link(self)
        count = 0
        for j in link_list:
            if j == "" or j == "#" or j == '#javascript::void(0)' or j == '#content' or j == '#skip' or j == 'javascript:;' or j == 'javascript::void(0);' or j == 'javascript::void(0)':
                count += 1
        if len(link_list) == 0:
            return 0
        return count
    

    # ----------------------------form based---------------------------------------------------

    def find_form(self):
        soup = self.text
        forms = soup.find_all('form')
        data = []

        for form in forms:
            input_tags = form.find_all('input')
            for input_tag in input_tags:
                try:
                    if str(input_tag).find('name'):
                        data.append((str(input_tag['name'])))
                    # if input_tag.has_key('name'):
                    #     data.append(str(input_tag['name']))
                except:
                    continue

        return data

    def login_form(self):  ## have login-form requires password
        input_list = html_check.find_form(self)
        result = 0
        for j in input_list:
            if j.find("password") != -1 or j.find("pass") != -1 or j.find("login") != -1 or j.find("signin") != -1:
                result = 1
                break
        return result
    



    def internal_external_resource(self):  ##
        tag_list = ['link', 'img', 'script', 'noscript']
        resource_list = []
        count = 0
        for tag in tag_list:
            resource_list.append(html_check.find_source(self, tag))

        resource_list = [y for x in resource_list for y in x]
        if len(resource_list) == 0:  ## in case there is no resource link
            return [0, 0]

        for j in resource_list:
            if "http" in j:
                if not (self.domain == tldextract.extract(j).domain):
                    count += 1

        return len(resource_list) - count, count

    # -----------------suspicious element HTML-------------------------------------------------

    def redirect(self):  ##auto-refresh webpage
        soup = self.text
        return int('redirect' in soup)

    def alarm_window(self):  ## alert window pop up
        soup = self.text
        scripts = soup.find_all('script')
        find = 0
        for script in scripts:
            try:
                if ('alert' in str(script.contents)) or ('window.open' in str(script.contents)):
                    find = 1
                    break
            except:
                continue

        return find

    # ---------------------------------domain vs HTML content----------------------------------------
    def title_domain(self):
        soup = self.text
        try:
            return int(self.domain.lower() in soup.title.text.lower())
        except:
            return 0

    # def domain_occurrence(self):
    #     try:
    #         return str(self.text).count(self.domain)
    #     except:
    #         return 0

    def brand_freq_domain(self):
        link_list = html_check.find_all_link(self)
        domain_list = []

        for j in link_list:
            if "http" in j:
                brand = tldextract.extract(j).domain
                domain_list.append(brand)
            else:
                domain_list.append(self.domain)

        if len(domain_list) == 0:
            return 1
        if pd.Series(domain_list).value_counts().index[0] == self.domain:
            return 1
        else:
            return 0
        

    #--------------------Functions By Duddu Hriday----------------------------------------------
    
    def pre_at_urls(self):
        return_links = []
        links = html_check.find_all_link(self)
        # Define a function to process each link
        def process_link(link):
            links_with_at = link.split('@')
            if len(links_with_at) > 1:
                return links_with_at[0]
            return None
        # Using ThreadPoolExecutor to parallelize processing of links
        with ThreadPoolExecutor() as executor:
            # Submitting tasks using executor.submit
            futures = [executor.submit(process_link, link) for link in links]
            # Iterating over completed futures
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    return_links.append(result)
        return return_links


    def is_link_valid(self):
        anchor_links = html_check.find_all_link(self)
        links_prefix_at = html_check.pre_at_urls(self)
        links = anchor_links + links_prefix_at
        good_links = 0
        bad_links = 0

        def check_link(link):
            # Ensure link is not empty before checking its first character
            if link and link[:5] != "https" and link[:5] != 'http:':
                if link[0] == '/':
                    link = self.url.rstrip('/') + link  # Properly handle trailing '/'
                else:
                    link = self.url.rstrip('/') + '/' + link  # Add '/' if not present

            if link[:4] != 'http':  # Ensure it starts with a valid protocol
                link = 'https://' + link.lstrip('/')  # Avoid double slashes

            try:
                response = requests.get(link, timeout=5)
                if response.status_code == 200:
                    return 'good'
                else:
                    return 'bad'
            except:
                return 'bad'

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(check_link, link): link for link in links}
            for future in as_completed(futures):
                result = future.result()
                if result == 'good':
                    good_links += 1
                else:
                    bad_links += 1

        return good_links, bad_links

    

    def multiple_https_check(self):
        links = html_check.find_all_link(self)
        for link in links:
            count = link.count('https:')
            if(count>1):
                return True
        return False
    
        # Form Based Feature
    def form_empty_action(self):
        soup = self.text
        forms = soup.find_all('form')
        for form in forms:
           action = form.attrs.get('action', '')
           if action=='"about: blank' or action == '':
               return True
        return False 
    
    def same_form_action_domain(self):
        soup = self.text
        forms = soup.find_all('form')
        for form in forms:
           action = form.attrs.get('action', '')
           parsed_action = urlparse(action)
           parsed_url = urlparse(self.url)
           url_domain = parsed_url.netloc
           form_domain = parsed_action.netloc
           if url_domain == form_domain or form_domain=='':
               return True
           return False
        

    def is_mail(self):
        soup = self.text
        pretty_soup = soup.prettify()
        if 'mail()' in pretty_soup or 'mailto:' in pretty_soup:
            return True
        return False

    # def num_of_redirects(self):
    #     try:
    #         # response = requests.get("https://" + self.url, allow_redirects=True)
    #         response = requests.get("https://" + self.url, allow_redirects=True, timeout=10)
    #         redirects = len(response.history)
    #         return redirects
    #     except:
    #         return -1
    
    def has_window_status(soup):
        # soup = self.text
        if 'windows.status' in soup.prettify():
            return True
        return False
    
    def status_bar_customization(self):
        soup = self.text
        anchor_tags = soup.find_all('a')
    
        for tag in anchor_tags:
            if tag.has_attr('onmouseover'):
                window_status = html_check.has_window_status(soup)
                return window_status
            
        return False


def main_fun(main_folder):
    html_features_list = []
    # tld_path_here = "tld.csv"
    # if os.path.exists("legitimate_resources"):
    #     main_folder = "legitimate_resources"
    #     info_csv = os.path.join("legitimate_resources", "info.csv")
    # # Check if phishing_resources folder exists
    # elif os.path.exists("phishing_resources"):
    #     main_folder = "phishing_resources"
    #     info_csv = os.path.join("phishing_resources", "info.csv")
    info_csv = os.path.join(main_folder,"info.csv")

    count  = 0

    start_time = time.time()
    with open(info_csv,'r') as file:
        for line in file.readlines():
            if count== 0:
                count = 1
                continue

            index = line.split(',')[0]
            url = line.split(',')[1]
            html_folder = line.split(',')[2].strip()
            print(url)
            if os.path.exists(html_folder):
                soup = read_html_file(html_folder)
                if len(soup) == 0:
                    content = ''
                else:
                    content = soup
            else:
                content = ''

            '''extract html features'''
            if len(content) == 0:
                features = {
                    'url': url,
                    'internal_link': '-',
                    'external_link': '-',
                    'empty_link': '-',
                    'login_form': '-',
                    'html_len_tag': '-',
                    'html_len': '-',
                    'alarm_window': '-',
                    'redirection': '-',
                    'hidden': '-',
                    'title_domain': '-',
                    'internal_resource': '-',
                    'external_resource': '-',
                    # 'domain_occurrence': '-',
                    'brand_domain': '-',
                    'working_links': '-',
                    'not_working_links': '-',
                    'multiple_https': '-',
                    'form_empty_action': '-',
                    'same_form_action_domain': '-',
                    'is_mail': '-',
                    # 'num_of_redirects': '-',
                    'status_bar_customization':'-'
                }
            else:
                test = html_check(content, url)
                features = {
                    'url': url,
                    'internal_link': test.internal_external_link()[0],
                    'external_link': test.internal_external_link()[1],
                    'empty_link': test.empty_link(),
                    'login_form': test.login_form(),
                    'html_len_tag': test.len_html_tag(),
                    'html_len': test.len_html(),
                    'alarm_window': test.alarm_window(),
                    'redirection': test.redirect(),
                    'hidden': test.hidden(),
                    'title_domain': test.title_domain(),
                    'internal_resource': test.internal_external_resource()[0],
                    'external_resource': test.internal_external_resource()[1],
                    # 'domain_occurrence': test.domain_occurrence(),
                    'brand_domain': test.brand_freq_domain(),
                    'working_links': test.is_link_valid()[0],
                    'not_working_links': test.is_link_valid()[1],
                    'multiple_https': test.multiple_https_check(),
                    'form_empty_action': test.form_empty_action(),
                    'same_form_action_domain': test.same_form_action_domain(),
                    'is_mail': test.is_mail(),
                    # 'num_of_redirects': test.num_of_redirects(),
                    'status_bar_customization': test.status_bar_customization()
                }

            html_features_list.append(features)
            # print(html_features_list)
    end_time = time.time()
    print("Total Time = "+ str(end_time - start_time))
    return html_features_list
    

