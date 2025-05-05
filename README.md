# Firecrawl Website Scraper

Scrapes URLs from `links.txt` using Firecrawl API, organizing output by domain and path.

## Setup

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure `.env`:** Create a `.env` file in the project root with:
    ```dotenv
    FIRECRAWL_API_KEY='YOUR_API_KEY'
    API_URL='YOUR_API_URL' # e.g., 'https://api.firecrawl.dev'
    ```

## Usage

1.  Populate `links.txt` with URLs (one per line).
2.  Run the script:
    ```bash
    python main.py
    ```

## Output

Scraped markdown files are saved in `./output/<domain>/<sanitized_path>.md`.

---