# KOSINTER -- OSINT Username Enumeration Tool

KOSINTER is a Python-based OSINT tool that checks whether a given
username exists across multiple platforms, including Instagram,
Twitter/X, Facebook, TikTok, Reddit, GitHub, GitLab, YouTube, and more.

The script generates username variants and examines each service using
platform-specific heuristics or APIs.\
Useful for OSINT investigations, security research, digital footprint
analysis, or username availability checks.

------------------------------------------------------------------------

## 🚀 Features

-   Checks usernames across multiple social media platforms
-   Instagram API-based detection for high accuracy
-   Twitter/X HTML analysis for conservative validation
-   Smart username variant generator (`base`, `dotted`, `dashed`,
    `underscored`, merged)
-   Color-coded CLI output
-   Handles redirects, HTTP errors, and edge cases
-   Interactive scanning loop

------------------------------------------------------------------------

## 📦 Supported Platforms

-   Instagram\
-   Twitter / X\ (will be released soon)
-   Facebook\ (will be released soon)
-   TikTok\ (will be released soon)
-   Reddit\
-   YouTube\
-   GitHub\
-   GitHub Gist\
-   GitLab\
-   Snapchat

------------------------------------------------------------------------

## 🛠️ Installation

### 1. Clone the repository

``` bash
git clone https://github.com/yourusername/kosinter.git
cd kosinter
```

### 2. Install dependencies

``` bash
pip install requests
pip install re
```

------------------------------------------------------------------------

## ▶️ Usage

Run the script with Python:

``` bash
python3 kosinter.py
```

You will be prompted:

    OSINT > Enter base username:

Then the tool:

-   Generates username variants
-   Checks multiple social platforms
-   Prints results with FOUND / not found indicators

------------------------------------------------------------------------

## 📁 Project Structure

    .
    ├── kosinter.py
    └── requirements.txt

------------------------------------------------------------------------

## 📜 Example Output

    --- Username variant: john_doe ---
    [+] Instagram       FOUND  -> https://instagram.com/john_doe
    [-] Twitter         not found
    [-] TikTok          not found
    [+] GitHub          FOUND  -> https://github.com/john_doe

------------------------------------------------------------------------

## 🤝 Contributing

Pull requests are welcome!\
If you'd like to contribute, improve heuristics, or add new platforms,
feel free to fork the repository.

------------------------------------------------------------------------

## 📄 License

MIT License (or any license you prefer).
