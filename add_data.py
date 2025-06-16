#uses os, time, uuid, requests, chromadb
from pathlib import Path
from bs4 import BeautifulSoup
import fitz  # PyMuPDF

# --- Configuration ---
CHROMA_PATH = "SecDB"
COLLECTION_NAME = "SecData"
URL_LIST_FILE = "urls.txt"
LOCAL_DATA_FOLDER = "loc_data"

# --- PART 1: WEB SCRAPING LOGIC ---
def scrape_and_add_url(url: str, collection):
    """
    Scrapes a single URL, extract text, add it to the Chroma collection
    """
    print(f"\n-> Processing URL: {url}")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        documents = [p.get_text().strip() for p in soup.find_all('p') if p.get_text().strip()]

        if not documents:
            print("  - No extractable paragraph text found.")
            return False

        print(f"  + Found {len(documents)} paragraphs. Adding to database...")
        ids = [f"url_{uuid.uuid5(uuid.NAMESPACE_URL, doc)}" for doc in documents]
        collection.add(documents=documents, ids=ids, metadatas=[{"source": url}] * len(documents))
        print("  ✔ Successfully added content.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"  ! Error fetching or processing URL {url}: {e}")
        return False

# --- PART 2: LOCAL FILE PROCESSING LOGIC ---
def get_text_from_file(filepath: Path):
    """Extracts text from a file, supporting .txt and .pdf."""
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
    """Processes files in the local data folder."""
    local_path = Path(LOCAL_DATA_FOLDER)
    if not local_path.exists():
        print(f"\nError: The local data folder '{LOCAL_DATA_FOLDER}' was not found.")
        print("Please create it and add your files.")
        return

    print(f"\nScanning for files in '{LOCAL_DATA_FOLDER}'...")
    supported_files = list(local_path.glob("*.pdf")) + list(local_path.glob("*.txt"))

    for filepath in supported_files:
        # --- Duplicate/Modification Check ---
        file_mod_time = filepath.stat().st_mtime
        
        # Check if a document already exists and get its mod time
        existing_docs = collection.get(where={"source_file": str(filepath)})
        if existing_docs['ids']:
            stored_mod_time = existing_docs['metadatas'][0].get('file_last_modified', 0)
            if file_mod_time <= stored_mod_time:
                print(f"  - Skipping '{filepath.name}', no changes detected.")
                continue
            else:
                print(f"  ! Detected changes in '{filepath.name}'. Updating entries...")
                collection.delete(where={"source_file": str(filepath)})

        # --- Process and Add New/Modified File ---
        print(f"  + Processing '{filepath.name}'...")
        text = get_text_from_file(filepath)
        if not text:
            print(f"  ! Could not extract text from '{filepath.name}'.")
            continue
            
        # --- Chunking Logic ---
        # Instead of adding the whole file, we split it into smaller chunks.
        # A good starting strategy is to split by paragraphs.


from langchain.text_splitter import RecursiveCharacterTextSplitter

		# 1. Text splitter
		text_splitter = RecursiveCharacterTextSplitter(
			chunk_size=1000,  # The target size of each chunk in characters
			chunk_overlap=200   # The number of characters to overlap between chunks
		)
		chunks = text_splitter.split_text(text)

        # 2. Prepare for batch adding to ChromaDB
        ids_list = []
        metadatas_list = []
        
        for i, chunk in enumerate(chunks):
            # Create chucnk unique IDs
            chunk_id = f"file_{filepath.name}_mod_{file_mod_time}_chunk_{i+1}"
            ids_list.append(chunk_id)

            # Each chunk from the same file shares the same metadata
            # but also gets its own chunk number
            chunk_metadata = {
                "source_file": str(filepath),
                "file_last_modified": file_mod_time,
                "chunk_number": i + 1
            }
            metadatas_list.append(chunk_metadata)
        
        # 3. Add all the chunks, IDs, and metadata to the collection
        collection.add(
            documents=chunks,
            ids=ids_list,
            metadatas=metadatas_list
        )
        
        print(f"  ✔ Successfully added {len(chunks)} chunks from '{filepath.name}' to the database.")


# --- PART 3: MAIN INTERACTIVE SCRIPT ---
def main():
    """Main function to run the interactive importer."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    print("\n--- Interactive Data Importer for RAG ---")
    print("Please choose an option:")
    print("  [1] Add a single URL")
    print(f"  [2] Process all URLs from '{URL_LIST_FILE}'")
    print(f"  [3] Process local files from './{LOCAL_DATA_FOLDER}/' folder")

    choice = input("Enter your choice (1, 2, or 3): ")
    start_time = time.time()

    if choice == '1':
        single_url = input("Please enter the URL to scrape: ").strip()
        if single_url:
            scrape_and_add_url(single_url, collection)
        else:
            print("No URL entered. Exiting.")

    elif choice == '2':
        if not os.path.exists(URL_LIST_FILE):
            print(f"\nError: The file '{URL_LIST_FILE}' was not found.")
            return
        with open(URL_LIST_FILE, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        for url in urls:
            scrape_and_add_url(url, collection)

    elif choice == '3':
        process_local_folder(collection)

    else:
        print("Invalid choice. Please run the script again.")

    end_time = time.time()
    print(f"\nFinished operation in {end_time - start_time:.2f} seconds.")


if __name__ == "__main__":
    main()