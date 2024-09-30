# Phish-Blitz

Phish-Blitz is a powerful tool designed to detect phishing websites by downloading and analyzing various web resources like HTML, JavaScript, CSS, images, favicons, and screenshots. This tool is intended for researchers and developers working on phishing website detection using Deep Learning (DL) and Machine Learning (ML) models.

## Features
- Fetches legitimate URLs based on page rank and phishing URLs from PhishStats.
- Downloads essential web resources such as HTML, CSS, JavaScript, images, and favicons.
- Redirects resources to local storage for offline access.
- Captures and stores website screenshots for comparison and analysis.
- Processes thousands of URLs efficiently in under 50 seconds.
- Offers comprehensive dataset creation for phishing and legitimate websites, helping researchers analyze and train detection models.

## Requirements
- **Operating System**: Linux (Ubuntu recommended)
- **Python**: Python 3.x
- **Package Manager**: `pip` (for installing Python dependencies)

### Python Packages
All the required packages are listed in the `requirements.txt` file.

## How to Run

Follow these simple steps to set up and run Phish-Blitz on your system:

1. **Clone the repository**:
    ```bash
    git clone https://github.com/Duddu-Hriday/Phish-Blitz.git
    ```

2. **Navigate to the project directory**:
    ```bash
    cd Phish-Blitz
    ```

3. **Install the required dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Run the application**:
    ```bash
    python3 app.py
    ```

That's it! Phish-Blitz will now begin processing URLs and downloading web resources.

## Contributing
We welcome contributions from the community! If you'd like to contribute:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and submit a pull request.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Developed by **Duddu Hriday** as a contribution to phishing website detection research.

For more details, visit [Phish-Blitz GitHub Repository](https://github.com/Duddu-Hriday/Phish-Blitz).
