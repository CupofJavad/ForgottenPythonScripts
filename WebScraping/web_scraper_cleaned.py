
import requests
from bs4 import BeautifulSoup
import os
import urllib.parse


def normalize_url(base_url, url):
    print(f"  [normalize_url] base_url: {base_url}, url: {url}")
    base_parsed = urllib.parse.urlparse(base_url)
    parsed_url = urllib.parse.urlparse(url)

    scheme = base_parsed.scheme
    netloc = parsed_url.netloc or base_parsed.netloc
    path = parsed_url.path.rstrip('/')
    params = parsed_url.params
    query = parsed_url.query
    fragment = ''

    normalized_url = urllib.parse.urlunparse((scheme, netloc, path, params, query, fragment))
    print(f"  [normalize_url] Normalized URL: {normalized_url}")
    return normalized_url


def find_internal_links(base_url, max_links=100):
    try:
        domain = urllib.parse.urlparse(base_url).netloc
        print(f"Scanning domain: {domain}")
        visited_urls = set()
        normalized_base_url = normalize_url(base_url, base_url)
        unvisited_urls = {normalized_base_url}
        all_internal_links = set()

        print(f"  [find_internal_links] Initial unvisited_urls: {unvisited_urls}")

        while unvisited_urls and len(all_internal_links) < max_links:
            current_url = unvisited_urls.pop()
            current_url = normalize_url(base_url, current_url)
            print(f"  Checking: {current_url}")
            if current_url in visited_urls:
                print("    Already visited")
                continue

            try:
                response = requests.get(current_url)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                visited_urls.add(current_url)

                print(f"  [find_internal_links] Finding links in: {current_url}")
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    print(f"  [find_internal_links] Found href: {href}")
                    full_url = urllib.parse.urljoin(current_url, href)
                    normalized_full_url = normalize_url(base_url, full_url)
                    parsed_full_url = urllib.parse.urlparse(full_url)

                    if parsed_full_url.netloc == domain and normalized_full_url not in all_internal_links:
                        print(f"    Found internal link: {normalized_full_url}")
                        all_internal_links.add(normalized_full_url)
                        unvisited_urls.add(normalized_full_url)

            except requests.exceptions.RequestException as e:
                print(f"Error fetching URL {current_url}: {e}")
            except Exception as e:
                print(f"An error occurred while processing {current_url}: {e}")

        print(f"Found {len(all_internal_links)} internal links.")
        return all_internal_links

    except Exception as e:
        print(f"An error occurred during the link discovery process: {e}")
        return set()


def scrape_text(url, filename="scraped_text.txt"):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        for script in soup.find_all(['script', 'style']):
            script.extract()

        text_parts = soup.stripped_strings
        visible_text = "\n".join(text_parts)

        with open(filename, 'w', encoding='utf-8') as file:
            file.write(visible_text)

        print(f"Successfully scraped text from {url} and saved to {filename}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
    except Exception as e:
        print(f"An error occurred during scraping or saving: {e}")


def scrape_domain_text(base_url, output_directory="scraped_content"):
    while True:
        output_dir = input("Enter the name of the directory to save the scraped content (or 'new' to create a new directory): ")
        if output_dir.lower() == 'new':
            output_dir = input("Enter the name for the new directory: ")
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir)
                    print(f"Directory '{output_dir}' created successfully.")
                    break
                except OSError as e:
                    print(f"Error creating directory '{output_dir}': {e}")
                    print("Please try again.")
            else:
                print(f"Directory '{output_dir}' already exists. Please choose a different name.")
        elif os.path.exists(output_dir):
            break
        else:
            print(f"Directory '{output_dir}' does not exist.")

    internal_links = find_internal_links(base_url)
    print(f"Found {len(internal_links)} internal links on {base_url}")

    for link in internal_links:
        parsed_link = urllib.parse.urlparse(link)
        path = parsed_link.path.replace("/", "_")
        if not path:
            path = "homepage"
        filename = os.path.join(output_dir, f"{parsed_link.netloc}{path}.txt")
        scrape_text(link, filename)


if __name__ == "__main__":
    print("What would you like to do?")
    print("1. Scrape text from a single URL")
    print("2. Scan a domain and scrape text from all internal pages")

    choice = input("Enter your choice (1 or 2): ")

    if choice == '1':
        url_to_scrape = input("Enter the URL to scrape: ")
        output_filename = input("Enter the desired filename (e.g., output.txt): ")
        scrape_text(url_to_scrape, output_filename)
    elif choice == '2':
        domain_to_scan = input("Enter the base URL of the domain to scan (e.g., https://help.current-rms.com/en/): ")
        scrape_domain_text(domain_to_scan)
    else:
        print("Invalid choice.")
