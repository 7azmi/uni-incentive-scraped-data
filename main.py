import os
import re # Import the regular expression module for sanitization
from firecrawl import FirecrawlApp
from dotenv import load_dotenv
from urllib.parse import urlparse
import tldextract

# --- Load Environment Variables ---
# Look for a .env file in the current directory and load variables from it
load_dotenv()
print("📦 Attempting to load environment variables from .env file.")

# --- Configuration ---
# Get configuration from environment variables (loaded from .env or system)
API_KEY = os.getenv("FIRECRAWL_API_KEY")
API_URL = os.getenv("API_URL")

INPUT_FILENAME = "links.txt"

# Dynamic output directory relative to the script's location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_OUTPUT_FOLDER_NAME = "output" # Name for the main output folder
MAIN_OUTPUT_DIRECTORY = os.path.join(SCRIPT_DIR, MAIN_OUTPUT_FOLDER_NAME)

# Define characters to replace in the URL path for filenames
# Common problematic characters across file systems: / \ : * ? " < > |
# We'll replace them with underscores
REPLACE_CHARS_PATTERN = re.compile(r'[\/:*?"<>|]')

def sanitize_url_path_for_filename(path):
    """Sanitizes a URL path to be safe for use as a filename base."""
    # Handle the root path specifically
    if path == '/' or path == '':
        return 'index'

    # Remove leading/trailing slashes that might cause issues or look odd
    sanitized_path = path.strip('/')

    # Replace problematic characters with underscore
    sanitized_path = REPLACE_CHARS_PATTERN.sub('_', sanitized_path)

    # Optional: Replace sequences of underscores with a single underscore
    # sanitized_path = re.sub(r'_{2,}', '_', sanitized_path)

    # Optional: Trim leading/trailing underscores resulting from replacements
    # sanitized_path = sanitized_path.strip('_')
    # If stripping made it empty (e.g. path was just '///'), revert to 'index'
    # if not sanitized_path:
    #    return 'index'


    # Ensure the filename is not empty after sanitization (unlikely with path!= '/')
    if not sanitized_path:
         return 'untitled' # Fallback filename

    return sanitized_path

# --- Check Configuration ---
if not API_KEY:
    print("❌ ERROR: FIRECRAWL_API_KEY not found in environment variables or .env file.")
    print("Please set the FIRECRAWL_API_KEY environment variable or add FIRECRAWL_API_KEY='your_api_key_here' to a .env file in the script directory.")
    exit(1)

if not API_URL:
     print("❌ ERROR: API_URL not found in environment variables or .env file.")
     print("Please set the API_URL environment variable or add API_URL='your_api_url_here' to a .env file in the script directory.")
     exit(1)

print("✅ Configuration loaded.")

# --- Initialize FirecrawlApp ---
try:
    app = FirecrawlApp(api_key=API_KEY, api_url=API_URL)
    print("✅ FirecrawlApp initialized.")
except Exception as e:
    print(f"❌ ERROR: Failed to initialize FirecrawlApp. Details: {e}")
    # Check for common API key errors
    if "Unauthorized" in str(e):
        print("   Possible cause: Invalid or expired API key.")
    exit(1)

# --- Load URLs ---
try:
    with open(INPUT_FILENAME, 'r', encoding='utf-8') as file:
        urls = [line.strip() for line in file if line.strip()]
    if not urls:
        print(f"⚠️ No URLs found in input file '{INPUT_FILENAME}'.")
        exit(0)
    print(f"📄 Loaded {len(urls)} URLs from '{INPUT_FILENAME}'.")
    total_urls_loaded = len(urls) # Keep track of the total loaded
except FileNotFoundError:
    print(f"❌ ERROR: Input file '{INPUT_FILENAME}' not found in the script directory.")
    print(f"Make sure '{INPUT_FILENAME}' is in the same directory as the script.")
    exit(1)

# --- Ensure Main Output Directory Exists ---
if not os.path.exists(MAIN_OUTPUT_DIRECTORY):
    try:
        os.makedirs(MAIN_OUTPUT_DIRECTORY)
        print(f"📁 Created main output directory: {MAIN_OUTPUT_DIRECTORY}")
    except Exception as e:
        print(f"❌ ERROR: Could not create main output directory '{MAIN_OUTPUT_DIRECTORY}'. {e}")
        exit(1)
else:
     print(f"📁 Main output directory already exists: {MAIN_OUTPUT_DIRECTORY}")


# --- Initialize Stats Counters ---
skipped_pdf_count = 0
skipped_exists_count = 0
error_count = 0
successfully_scraped_count = 0

# --- Process Each URL ---
print("\nStarting processing...")
for idx, url in enumerate(urls, start=1):
    print(f"\n[{idx}/{total_urls_loaded}] Processing: {url}")

    # --- REQUIREMENT 1: Ignore PDF URLs ---
    if url.lower().endswith('.pdf'):
        print(f"   ➡️ Skipping URL ending in .pdf: {url}")
        skipped_pdf_count += 1 # Increment PDF skip counter
        continue # Skip to the next URL in the loop

    try:
        # --- Extract Registrable Domain using tldextract ---
        extracted = tldextract.extract(url)

        # Check if tldextract successfully found domain and suffix
        if not extracted.domain or not extracted.suffix:
             print(f"   ⚠️ Could not extract registrable domain from URL: {url}. Skipping.")
             error_count += 1 # Count this as an error in processing
             continue

        # Combine domain and suffix to get the folder name (e.g., 'taylors.edu.my', 'upm.edu.my')
        main_domain = f"{extracted.domain}.{extracted.suffix}"

        # Sanitize domain name for folder name (replace potential problematic characters if any)
        main_domain = main_domain.replace(':', '_').replace('/', '_') # Simple domain sanitization


        # --- Construct Domain-Specific Output Directory ---
        DOMAIN_OUTPUT_DIRECTORY = os.path.join(MAIN_OUTPUT_DIRECTORY, main_domain)

        # Ensure the domain-specific directory exists
        if not os.path.exists(DOMAIN_OUTPUT_DIRECTORY):
            try:
                os.makedirs(DOMAIN_OUTPUT_DIRECTORY)
                print(f"   Created domain directory: {DOMAIN_OUTPUT_DIRECTORY}")
            except Exception as e:
                print(f"   ❌ ERROR: Could not create domain directory '{DOMAIN_OUTPUT_DIRECTORY}'. Skipping URL. {e}")
                error_count += 1 # Count this as an error
                continue # Skip processing this URL if directory creation failed

        # --- Generate Filename from URL Path ---
        parsed_url = urlparse(url)
        filename_base = sanitize_url_path_for_filename(parsed_url.path)

        output_filename = f"{filename_base}.md"

        # Ensure the filename isn't excessively long (some OS limits)
        MAX_FILENAME_LEN = 200 # A common safe limit, adjust if needed
        if len(output_filename) > MAX_FILENAME_LEN:
            # Truncate and maybe add a hash to avoid collisions if needed
            # For simplicity, let's just truncate and add the index as a fallback identifier
            print(f"   ⚠️ Generated filename is too long ({len(output_filename)} chars), truncating.")
            # Keep the .md extension and leave space for index + underscore
            truncated_base = filename_base[:MAX_FILENAME_LEN - len('.md') - len(str(idx)) - 1]
            output_filename = f"{truncated_base}_{idx}.md"


        output_path = os.path.join(DOMAIN_OUTPUT_DIRECTORY, output_filename)

        # --- REQUIREMENT 2: Skip if output file already exists ---
        if os.path.exists(output_path):
            print(f"   ✅ Output file already exists: {output_path}. Skipping scraping.")
            skipped_exists_count += 1 # Increment exists skip counter
            continue # Skip the API call and file writing, move to next URL


        # --- Only scrape if it's not a PDF and the file doesn't exist ---
        print(f"   🌍 Crawling URL with Firecrawl: {url}") # Indicate when API call happens
        response = app.scrape_url(url, formats=["markdown"])

        # The response object directly has attributes like .markdown, .html, .data, etc.
        markdown_content = response.markdown

        if not markdown_content:
            print(f"   ⚠️ No markdown content returned for: {url}")
            error_count += 1 # Count empty content as an error/failure
            continue


        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"   💾 Saved: {output_path}") # Changed print for clarity
        successfully_scraped_count += 1 # Increment success counter

    except Exception as e:
        print(f"   ❌ ERROR processing {url}: {e}") # Changed 'scraping' to 'processing'
        error_count += 1 # Increment error counter

# --- Print Run Statistics ---
print("\n--- 📊 Run Statistics ---")
print(f"🔗 Total URLs Loaded: {total_urls_loaded}")
print(f"➡️ Skipped (PDF): {skipped_pdf_count}")
print(f"⏭️ Skipped (Already Exists): {skipped_exists_count}")
print(f"✅ Successfully Scraped & Saved: {successfully_scraped_count}")
print(f"❌ Errors (Processing/Scraping Failed): {error_count}")
print("-------------------------\n")

print("🎉 Processing completed.")