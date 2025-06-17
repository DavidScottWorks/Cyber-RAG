import os
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import chromadb
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter

# --- Configuration ---
CHROMA_PATH = "SecDB"
COLLECTION_NAME = "SecData"
URL_LIST_FILE = "urls.txt"
LOCAL_DATA_FOLDER = "loc_data"

#CENTRAL PROCESSING FOR ALL DATA SOURCES
def process_and_add_text(text: str, collection, source_metadata: dict):
    # chunk text and send it to database
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_text(text)

    if not chunks:
        return 0

    ids_list = []
    metadatas_list = []
    
    # Create source ID's from metadata
    source_name = Path(source_metadata.get("source_file") or source_metadata.get("source_url", "unknown")).name

    for i, chunk in enumerate(chunks):
        chunk_id = f"source_{source_name}_chunk_{i+1}"
        ids_list.append(chunk_id)
        
        chunk_metadata = source_metadata.copy()
        chunk_metadata['chunk_number'] = i + 1
        metadatas_list.append(chunk_metadata)
    
    collection.add(documents=chunks, ids=ids_list, metadatas=metadatas_list)
    return len(chunks)

#DATA TEXT EXTRACTION
def scrape_and_add_url(url: str, collection):
    print(f"\n-> Processing URL: {url}")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract text from paragraphs and join them into a single block
        paragraphs = [p.get_text().strip() for p in soup.find_all('p') if p.get_text().strip()]
        full_text = "\n\n".join(paragraphs)

        if not full_text:
            print("  - No extractable paragraph text found.")
            return

        # Prepare metadata and call the central processor
        metadata = {"source_url": url}
        num_chunks = process_and_add_text(full_text, collection, metadata)
        print(f"  ✔ Successfully added {num_chunks} chunks from '{url}'.")

    except requests.exceptions.RequestException as e:
        print(f"  ! Error fetching or processing URL {url}: {e}")

def get_text_from_file(filepath: Path):
    # Extract text from txt and pdf
    if filepath.suffix == ".txt":
        return filepath.read_text(encoding='utf-8')
    elif filepath.suffix == ".pdf":
        text = ""
        with fitz.open(filepath) as doc:
            for page in doc:
                text += page.get_text()
        return text
    return None

def process_local_folder(collection):
    #Pass extracted text to the central processor.
    local_path = Path(LOCAL_DATA_FOLDER)
    if not local_path.exists():
        print(f"\nError: The local data folder '{LOCAL_DATA_FOLDER}' was not found.")
        return

    print(f"\nScanning for files in '{LOCAL_DATA_FOLDER}'...")
    supported_files = list(local_path.glob("*.pdf")) + list(local_path.glob("*.txt"))

    for filepath in supported_files:
        file_mod_time = filepath.stat().st_mtime
        existing_docs = collection.get(where={"source_file": str(filepath)})
        if existing_docs['ids']:
            stored_mod_time = existing_docs['metadatas'][0].get('file_last_modified', 0)
            if file_mod_time <= stored_mod_time:
                print(f"  - Skipping '{filepath.name}', no changes detected.")
                continue
            else:
                print(f"  ! Detected changes in '{filepath.name}'. Updating entries...")
                collection.delete(where={"source_file": str(filepath)})

        print(f"  + Processing '{filepath.name}'...")
        text = get_text_from_file(filepath)
        if not text:
            print(f"  ! Could not extract text from '{filepath.name}'.")
            continue
        
        # Prepare metadata and call the central processor
        metadata = {"source_file": str(filepath), "file_last_modified": file_mod_time}
        num_chunks = process_and_add_text(text, collection, metadata)
        print(f"  ✔ Successfully added {num_chunks} chunks from '{filepath.name}'.")


# MAIN INTERACTIVE SCRIPT
def main():
    #Run the interactive importer with a loop."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    while True:
        print("\n--- Interactive Data Importer for RAG ---")
        print("Please choose an option:")
        print("  [1] Add a single URL")
        print(f"  [2] Process all URLs from {URL_LIST_FILE}")
        print(f"  [3] Process local files from {LOCAL_DATA_FOLDER} folder")
        print("  [4] Exit")

        choice = input("Enter your choice (1, 2, 3, or 4): ")

        if choice in ['1', '2', '3']:
            start_time = time.time()

            if choice == '1':
                single_url = input("Please enter the URL to scrape: ").strip()
                if single_url:
                    scrape_and_add_url(single_url, collection)
            
            elif choice == '2':
                if not os.path.exists(URL_LIST_FILE):
                    print(f"\nError: The file '{URL_LIST_FILE}' was not found.")
                    # Use 'continue' to skip the rest of this loop iteration
                    continue 
                with open(URL_LIST_FILE, 'r') as f:
                    urls = [line.strip() for line in f if line.strip()]
                for url in urls:
                    scrape_and_add_url(url, collection)
            
            elif choice == '3':
                process_local_folder(collection)

            end_time = time.time()
            print(f"\nFinished operation in {end_time - start_time:.2f} seconds.")

        elif choice == '4':
            # Loop exit
            print("Excellent choice. Exiting data importer.")
            break  # The 'break' keyword terminates the while loop.

        else:
            # Handle invalid choices
            print("\n[!] Invalid choice. Please select a number from 1 to 4.")
            time.sleep(3) # A short pause to let the user read the message.

if __name__ == "__main__":
    main()
