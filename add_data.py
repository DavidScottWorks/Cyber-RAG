import os
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import chromadb
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from collections import deque
from urllib.parse import urljoin, urlparse
import colorama
from colorama import Fore, Style

# Color Definitions for colorama
HEADING = Fore.YELLOW
WARNING = Fore.RED
SUCCESS = Fore.GREEN
INFO = Fore.CYAN
RESET = Style.RESET_ALL

# --- Configuration ---
CHROMA_PATH = "SecDB"
COLLECTION_NAME = "SecData"
URL_LIST_FILE = "urls.txt"
LOCAL_DATA_FOLDER = "loc_data"


# MAIN PROCESSING & DATA EXTRACTION

def process_and_add_text(text: str, collection, source_metadata: dict):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)
    if not chunks: return 0
    ids_list = []
    metadatas_list = []
    source_name = Path(source_metadata.get("source_file") or source_metadata.get("source_url", "unknown")).name
    for i, chunk in enumerate(chunks):
        chunk_id = f"source_{source_name}_chunk_{i+1}"
        ids_list.append(chunk_id)
        chunk_metadata = source_metadata.copy()
        chunk_metadata['chunk_number'] = i + 1
        metadatas_list.append(chunk_metadata)
    collection.add(documents=chunks, ids=ids_list, metadatas=metadatas_list)
    return len(chunks)

def get_text_from_file(filepath: Path):
    if filepath.suffix == ".txt": return filepath.read_text(encoding='utf-8')
    elif filepath.suffix == ".pdf":
        text = ""
        with fitz.open(filepath) as doc:
            for page in doc: text += page.get_text()
        return text
    return None

#LOCAL FILE PROCESSING
def process_local_folder(collection):
    #Pass extracted text to the central processor.
    local_path = Path(LOCAL_DATA_FOLDER)
    if not local_path.exists():
        print(f"\n{WARNING}Error: The local data folder- {LOCAL_DATA_FOLDER} -was not found{RESET}")
        return

    print(f"\n{INFO}Scanning for files in {LOCAL_DATA_FOLDER}...{RESET}")
    supported_files = list(local_path.glob("*.pdf")) + list(local_path.glob("*.txt"))

    for filepath in supported_files:
        file_mod_time = filepath.stat().st_mtime
        existing_docs = collection.get(where={"source_file": str(filepath)})
        if existing_docs['ids']:
            stored_mod_time = existing_docs['metadatas'][0].get('file_last_modified', 0)
            if file_mod_time <= stored_mod_time:
                print(f" {INFO} - Skipping {filepath.name}, no changes detected{RESET}")
                continue
            else:
                print(f"  {INFO} Detected changes in {filepath.name}. Updating entries{RESET}")
                collection.delete(where={"source_file": str(filepath)})

        print(f" {INFO} + Processing '{filepath.name}'...")
        text = get_text_from_file(filepath)
        if not text:
            print(f"  {WARNING}! Could not extract text from {filepath.name}{RESET}")
            continue
        
        # Prepare metadata and call the central processor
        metadata = {"source_file": str(filepath), "file_last_modified": file_mod_time}
        num_chunks = process_and_add_text(text, collection, metadata)
        print(f"  ✔ {SUCCESS}Successfully added {num_chunks} chunks from {filepath.name}{RESET}")


#-----------
#WEB SCRAPER
def scrape_page_and_get_links(url: str, collection):
    #Scrapes a single URL
    print(f"\n-> {INFO} Scraping: {url}")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        #Add text to database
        paragraphs = [p.get_text().strip() for p in soup.find_all('p') if p.get_text().strip()]
        full_text = "\n\n".join(paragraphs)
        if full_text:
            metadata = {"source_url": url}
            num_chunks = process_and_add_text(full_text, collection, metadata)
            print(f"  ✔ {SUCCESS}Added {num_chunks} chunks{RESET}")
        
        #Find valid links on the page
        links = set()
        for a_tag in soup.find_all('a', href=True):
            link = a_tag['href']
            # Join relative links (e.g., '/about') with the base URL
            absolute_link = urljoin(url, link)
            # Remove anchors and query parameters
            parsed_link = urlparse(absolute_link)
            clean_link = parsed_link._replace(query="", fragment="").geturl()
            links.add(clean_link)
        return list(links)

    except requests.exceptions.RequestException as e:
        print(f"{WARNING} ! Error during request: {e}{RESET}")
        return []

#---------
#RECURSIVE CRAWLER LOGIC
def recursive_scrape(start_url: str, max_links: int, collection):
    #Crawls a site, respects a link limit.
    
    base_domain = urlparse(start_url).netloc
    links_to_visit = deque([start_url])
    visited_links = set()
    scrape_count = 0
    
    if not start_url: return
       
    while links_to_visit and scrape_count < max_links:
        current_url = links_to_visit.popleft()
        if current_url in visited_links:
            continue

        # Check if the link is on the same domain before scraping
        if urlparse(current_url).netloc != base_domain:
            continue

        visited_links.add(current_url)
        scrape_count += 1

        new_links = scrape_page_and_get_links(current_url, collection)
        
        for link in new_links:
            if link not in visited_links:
                links_to_visit.append(link)
    
    print(f"\n{SUCCESS}--- Recursive scrape finished. Visited {scrape_count} pages. ---")

#----------
#MAIN INTERACTIVE SCRIPT

def main():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    while True:
        print(f"\n{HEADING}---IMPORT DATA FOR RAG DATABASE---{RESET}")
        print(f"{INFO}Please choose an option:{RESET}")
        print(f" [1] Process files from {LOCAL_DATA_FOLDER} folder")
        print(f" [2] Add a single webpage URL (No link following)")
        print(f" [3] Follow links from a starting URL (Web Crawler)")
        print(f" [4] Process all URLs from custom {URL_LIST_FILE}")
        print(" [5] Exit")

        choice = input("Enter your choice (1-5): ")
        
        # Start the timer if a valid choice is made
        if choice in ['1', '2', '3', '4']:
            start_time = time.time()
        else:
            if choice == '5':
                print(f"{INFO}Exiting program. Goodbye!{RESET}")
                break
            else:
                print(f"\n{WARNING}[!] Invalid choice. Please select a number from 1 to 5{RESET}")
                time.sleep(2)
                continue
        
        # --- Process Valid Choices ---
        if choice == '1':
            process_local_folder(collection)
        
        elif choice == '2':
            while True:
                url = input("Please enter the URL to scrape (or type 'back' to return to menu): ").strip()
                if url.lower() == 'back': break
                try:
                    result = urlparse(url)
                    if all([result.scheme, result.netloc]):
                        print("{INFO}  URL is valid. Proceeding with scrape...")
                        scrape_page_and_get_links(url, collection)
                        break 
                    else:
                        print(f"{WARNING} That's not a valid URL. Please input a URL.{RESET}")
                except ValueError:
                    print(f"{WARNING}  That's not a valid URL. Please input a URL{RESET}")

        elif choice == '3':
            start_url = ''
            while True:
                start_url = input("Enter the starting URL to crawl (or type 'back' to return to menu): ").strip()
                if start_url.lower() == 'back': break
                try:
                    result = urlparse(start_url)
                    if all([result.scheme, result.netloc]):
                        print(f"{INFO}   Starting URL is valid{RESET}")
                        break
                    else:
                        print(f"{WARNING}    That's not a valid URL. Please input a URL{RESET}")
                except ValueError:
                    print(f"{WARNING}    That's not a valid URL. Please input a URL{RESET}")
            
            if start_url.lower() == 'back':
                continue

            print(f"\n{HEADING} ---Choose a limit for the crawler:{RESET}")
            print("     [1]Default of 10 Links")
            print("     [2]Set Your Own Number")
            print("     [3]Crawl Every Link It Finds")
            limit_choice = input(f"{INFO}  Enter limit choice (1-3): {RESET}").strip()

            max_links = 0
            if limit_choice == '1':
                max_links = 10
            elif limit_choice == '2':
                try:
                    max_links = int(input("    Enter the maximum number of links to follow: "))
                except ValueError:
                    print(f"{WARNING}[!] Invalid number. Aborting crawl{RESET}")
                    continue
            elif limit_choice == '3':
                print(f"\n{WARNING}[!] WARNING: Unlimited scraping can take a very long time and consume a lot of resources{RESET}")
                confirm = input(f"{INFO}    Are you sure you want to proceed? (yes/no): {RESET}").lower().strip()
                if confirm in ['yes', 'y']:
                    max_links = float('inf')
                else:
                    print(f"{INFO}    Crawl aborted by user{RESET}")
                    continue
            else:
                print(f"{WARNING}[!] Invalid limit choice. Aborting crawl{RESET}")
                continue
            
            recursive_scrape(start_url, max_links, collection)

        elif choice == '4':
            if not os.path.exists(URL_LIST_FILE):
                print(f"\n{WARNING} Error: The file {URL_LIST_FILE} was not found{RESET}")
                continue 
            with open(URL_LIST_FILE, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            for url in urls: scrape_page_and_get_links(url, collection)

        end_time = time.time()
        print(f"\nFinished operation in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    main()
