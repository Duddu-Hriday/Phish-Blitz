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
import whois

import time

tld_path_here = "tld.csv"

class URL_check():

    def __init__(self, url):
        self.tldlist_path = tld_path_here
        self.url = url.lower()

    def domain_is_IP(self):

        if len(tldextract.extract(self.url).subdomain) == 0:
            hostname = tldextract.extract(self.url).domain
        else:
            hostname = '.'.join([tldextract.extract(self.url).subdomain, tldextract.extract(self.url).domain])

        if np.sum([i.isdigit() for i in hostname.split(".")]) == 4:
            return True
        else:
            return False

    def symbol_count(self):

        punctuation_list = ["@", '-', '~']
        count = 0
        for j in punctuation_list:
            if j in self.url:
                count += 1
        return count

    def https(self):
        return "https://" in self.url

    def domain_len(self):
        if len(tldextract.extract(self.url).subdomain) == 0:
            domain_len = len(tldextract.extract(self.url).domain + "." + tldextract.extract(self.url).suffix)
        else:
            domain_len = len(tldextract.extract(self.url).subdomain + "." + tldextract.extract(
                self.url).domain + "." + tldextract.extract(self.url).suffix)
        return domain_len

    def url_len(self):
        return len(self.url)

    def num_dot_hostname(self):
        if len(tldextract.extract(self.url).subdomain) == 0:
            hostname = tldextract.extract(self.url).domain
        else:
            hostname = '.'.join([tldextract.extract(self.url).subdomain, tldextract.extract(self.url).domain])
        return hostname.count('.')

    def sensitive_word(self):
        sensitive_list = ["secure", "account", "webscr", "login",
                          "signin", "ebayisapi", "banking", "confirm"]
        return (any(x in self.url for x in sensitive_list))

    def tld_in_domain(self):
        path = self.tldlist_path
        tld_list = list(pd.read_csv(path, encoding="ISO-8859-1").Domain.apply(lambda x: x.replace('.', '')))

        for tld in tld_list:
            if tld == tldextract.extract(self.url).subdomain or tld == tldextract.extract(self.url).domain:
                return 1
        return 0

    def tld_in_path(self):
        path = self.tldlist_path
        tld_list = list(pd.read_csv(path, encoding="ISO-8859-1").Domain.apply(lambda x: x.replace('.', '')))

        for tld in tld_list:
            if tld == urlparse(self.url).path or tld == urlparse(self.url).params or tld == urlparse(
                    self.url).query or tld == urlparse(self.url).fragment:
                return True
        return False

    #-------------Functions written by Duddu Hriday----------------------------------------------

    def https_in_domain(self):
        parsed_url = urlparse(self.url)
        domain = parsed_url.netloc
        if 'http' in domain or 'https' in domain:
            return True
        return False
    
    def abnormal_url(self):
        try:
            parsed_url = urlparse(self.url)
            domain = parsed_url.netloc
            whois_info  = whois.whois(self.url)
            hostnames = whois_info.domain_name
            if isinstance(hostnames, str):
                hostnames = [hostnames]
            for hostname in hostnames:
                if hostname.lower() == domain.lower():
                    return False
            return True
        except:
            return True
    def is_at_symbol_present(url):
        return '@' in url
    
    def targeted_domain(self):
        if(URL_check.is_at_symbol_present(self.url)):
            target_link = str(self.url).split('@')
            parsed_url = urlparse(target_link[0])
            url_domain = parsed_url.netloc
            return url_domain
        else:
            return "None"
        

def extract_features(urls):
    result = []
    start_time = time.time()
    
    for url_dict in urls:
        url = url_dict["url"]
        
        # Extract HTML features
        url_class = URL_check(url)
        domain_is_ip = url_class.domain_is_IP()
        symbol_count = url_class.symbol_count()
        http = url_class.https()
        domain_len = url_class.domain_len()
        url_len = url_class.url_len()
        num_dot_hostname = url_class.num_dot_hostname()
        sensitive_word = url_class.sensitive_word()
        tld_in_domain = url_class.tld_in_domain()
        tld_in_path = url_class.tld_in_path()
        https_in_domain = url_class.https_in_domain()
        abnormal_url = url_class.abnormal_url()
        
        # Create a dictionary of the features
        feature_dict = {
            "url": url,
            "domain_is_ip": domain_is_ip,
            "symbol_count": symbol_count,
            "http": http,
            "domain_len": domain_len,
            "url_len": url_len,
            "num_dot_hostname": num_dot_hostname,
            "sensitive_word": sensitive_word,
            "tld_in_domain": tld_in_domain,
            "tld_in_path": tld_in_path,
            "https_in_domain": https_in_domain,
            "abnormal_url": abnormal_url
        }
        
        # Append the dictionary to the result list
        result.append(feature_dict)
    
    return result

# urls = [
#     {"url": "http://example.com"},
#     {"url": "https://example.org"},
#     # Add more dictionaries as needed
# ]

# # Example usage
# features = extract_features(urls)
# for feature in features:
#     print(feature)