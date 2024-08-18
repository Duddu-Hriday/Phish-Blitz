import requests

def fetch_phishing_data(count):
    # URL of the CSV file
    csv_url = 'https://phishstats.info/phish_score.csv'
    
    # Download the CSV file content
    response = requests.get(csv_url)
    csv_content = response.text
    
    # Split the content into lines
    lines = csv_content.splitlines()
    
    # Initialize an empty list to store the phishing data as dictionaries
    phishing_data = []
    
    # Skip the first 10 lines and process the remaining ones
    for line in lines[9:]:
        # Split the line by commas to extract the necessary fields
        fields = line.split(',')
        if len(fields) >= 4:  # Ensure there are at least 4 fields
            try:
                date = fields[0].strip('"')   # Extract the Date
                score = float(fields[1].strip('"'))  # Convert the Score to a float
                url = fields[2].strip('"')    # Extract the URL
                ip = fields[3].strip('"')     # Extract the IP address
                if score > 4:  # Check if the score is greater than 4
                    phishing_data.append({
                        "Date": date,
                        "Score": score,
                        "url": url,
                        "IP": ip
                    })
                    if len(phishing_data) == count:  # Stop if the desired count is reached
                        break
            except ValueError:
                # Handle cases where the score is not a valid float
                continue

    return phishing_data

# Example usage
# phishing_list = fetch_phishing_data(5)
# print(phishing_list)

# # You can also write this data to a file if needed
# with open('phishstats.txt', 'w') as file:
#     for entry in phishing_list:
#         file.write(f"{entry}\n")

# print("Filtered phishing data has been extracted and stored in 'phishstats.txt'")
