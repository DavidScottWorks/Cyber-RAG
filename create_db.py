#chromadb, requests, beautifulsoup4, PyMuPDF

#create db names SecDB
client = chromadb.PersistentClient(path="SecDB")

#create temp in-memory only db
#client=chromadb.Client() 

collection =client.get_or_create_collection(name='SecData")

#add data
print("Adding documents...")
collection.add(
	document=[
		XXXXXXXXXXX
	].
	ids=["xxxxxx"]
)
print("Data added")

