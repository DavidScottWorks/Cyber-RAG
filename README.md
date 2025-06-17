# Cyber-RAG
Set up for a cybersecurity RAG using ChromaDB. Meant to be connected to by a LLM. I'm building out the needed 'modules' as I go, including the ones which evolve for better functionality (i.e. scope creep). These are all meant to connect together eventually.
---
CreateDB <-- Creates the initial ChromaDB, named SecDB
---
dep_check <-- Checks dependencies and asks to install needed ones
---
add_data <-- Parses and chunks txt and PDF's from a local folder (loc_data), a single URL or a URL text file and adds it to the database
---
