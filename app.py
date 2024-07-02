from flask import Flask, render_template, request
import time
from concurrent.futures import ThreadPoolExecutor
from phish_tank_scraper import fetch_and_scrape_page
from feature_extraction import extract_features
app = Flask(__name__)

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
    print(legitimate_urls_dict)
    
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



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
