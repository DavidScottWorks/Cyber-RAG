# Cyber-RAG
Set up for a cybersecurity RAG using ChromaDB. Meant to be connected to by a LLM. I'm building out the needed 'modules' as I go, including the ones which evolve for better functionality (i.e. scope creep). These are all meant to connect together eventually.
---
dep_check <-- Checks dependencies and asks to install needed ones
---
create_db <-- Creates the ChromaDB. Default name is SecDB. You can create and/or override new databases with different names for each.
---
add_data <-- Parse and chunk txt and PDF's from a local folder (default: loc_data), a single URL or a URL text file and adds it to the database
---
