from flask import Flask, render_template, request
import time
from concurrent.futures import ThreadPoolExecutor
from phish_tank_scraper import fetch_and_scrape_page

app = Flask(__name__)

@app.route("/")
def home_page():
    return render_template('home.html')

@app.route("/fetch-urls")
def fetch_urls_page():
    return render_template("urls.html")

@app.route("/phishing-urls", methods=["POST"])
def phishing_urls():
    user_input = request.form['userInput']
    data = []
    day = 0
    pages = int(user_input)

    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(fetch_and_scrape_page, day, page, data) for page in range(pages)]

        # Ensure all threads have completed
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"Thread resulted in an error: {e}")

    print(data)

    # Do something with user_input, such as processing or storing it
    return render_template("phishing-urls.html",urls = data)

@app.route("/legitimate-urls", methods = ["POST"])
def legitimate_urls():
    with open('urls.txt', 'r') as file:
        urls = file.readlines()
    user_input = request.form['userInputLegit']
    return render_template('legitimate-urls.html',count = int(user_input),urls = urls)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
