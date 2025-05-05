import os
import time
import tldextract
from firecrawl import FirecrawlApp
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
api_key = os.getenv("FIRECRAWL_API_KEY")
app = FirecrawlApp(api_key=api_key)

# Load URLs from links.txt
with open("links.txt", "r") as f:
    urls = [line.strip() for line in f if line.strip()]

# Submit batch scrape job
job = app.async_batch_scrape_urls(urls, formats=['markdown'])

# Poll until job is complete
while True:
    status = app.check_batch_scrape_status(job.id)
    if status["status"] == "completed":
        break
    print("Waiting for job to complete...")
    time.sleep(5)

# Helper function to extract domain (ignoring subdomain)
def get_domain(url):
    ext = tldextract.extract(url)
    return ext.domain + "." + ext.suffix

# Save each result
for item in status["data"]:
    markdown = item["markdown"]
    metadata = item["metadata"]
    source_url = metadata["sourceURL"]
    domain = get_domain(source_url)
    title = metadata.get("title", "untitled").replace(" ", "_").replace("/", "_")[:50]

    folder_path = os.path.join("output", domain)
    os.makedirs(folder_path, exist_ok=True)

    filename = f"{title}.md"
    file_path = os.path.join(folder_path, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"Saved: {file_path}")
