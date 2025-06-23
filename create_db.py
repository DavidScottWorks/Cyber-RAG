import chromadb
import os
import sys
import shutil
import colorama
from colorama import Fore, Style

# Colorama color Definitions
HEADING = Fore.YELLOW
WARNING = Fore.RED
SUCCESS = Fore.GREEN
INFO = Fore.CYAN
RESET = Style.RESET_ALL


def create_chroma_db():
    #Guides user through creating a persistent ChromaDB database and collection
    
    # Default names for database and collection
    default_db_path = "SecDB"
    default_collection_name = "SecData"

    db_path = ""
    collection_name = ""

    #Step 1: Check if default database exists
    if os.path.isdir(default_db_path):
        print(f"\n{HEADING}================================{RESET}")
        print(f"\n{HEADING}Database {RESET}{default_db_path} {HEADING}already exists{RESET}")
        print(f"\n{HEADING}================================{RESET}")
        
        while True:
            #Ask user what action to take
            print(f"\n{INFO}Please choose an option:{RESET}")
            print(f"  [ 1 ] Override the existing database {WARNING}(WARNING: all data will be lost){RESET}")
            print("  [ 2 ] Create a new database with a different name")
            print("  [ 3 ] Exit the program")
            choice = input(f"\n{INFO}Enter your choice {RESET} 1, 2, or 3: ")

            if choice == '1':
                # --- Override existing default database ---
                print(f"\n{WARNING}WARNING: This action is irreversible and will delete all existing data{RESET}")
                confirm_override = input(f"{INFO}Are you SURE you want to proceed?{RESET} (yes/no): ").lower()
                if confirm_override in ['yes', 'y']:
                    try:
                        print(f"{INFO}Deleting existing database directory '{default_db_path}'...{RESET}")
                        shutil.rmtree(default_db_path)
                        print(f"{SUCCESS}Deletion successful{RESET}")
                        db_path = default_db_path
                        break # Exit the menu loop, go to collection creation
                    except Exception as e:
                        print(f"{WARNING}Error deleting directory: {e}{RESET}")
                        sys.exit()
                else:
                    print(f"{INFO}Override cancelled. Returning to main menu{RESET}")
                    continue # return to start of the menu loop

            elif choice == '2':
                #Create a new database with a custom name
                while True: # Loop to allow user to try different names
                    new_db_path = input(f"\nEnter the name for the new database directory (cannot be '{default_db_path}'): ")
                    if not new_db_path:
                        print(f"{INFO}Database name cannot be empty{RESET}")
                        continue
                    elif new_db_path == default_db_path:
                        print(f"{WARNING}'{default_db_path}' cannot be used. Please choose a different name{RESET}")
                        continue
                    
                    # Check custom-named database already exists
                    if os.path.isdir(new_db_path):
                        print(f"\n{WARNING}Warning: A database directory named '{new_db_path}' already exists{RESET}")
                        overwrite_choice = input("\nDo you want to overwrite it? (yes/no): ").lower()
                        if overwrite_choice in ['yes', 'y']:
                            try:
                                print(f"{WARNING}Deleting existing database directory '{new_db_path}'...{RESET}")
                                shutil.rmtree(new_db_path)
                                print(f"{SUCCESS}Deletion successful{RESET}")
                                db_path = new_db_path
                                break # Exit 'try different names' loop
                            except Exception as e:
                                print(f"{WARNING}Error deleting directory: {e}{RESET}")
                                sys.exit()
                        else:
                            print(f"\n{INFO}Please choose an option{RESET}")
                            print("  [ 1 ] Try another name")
                            print("  [ 2 ] Exit the program")
                            exit_choice = input(f"{INFO}Enter your choice (1 or 2):{RESET}")
                            if exit_choice == '2':
                                print(f"{INFO}Exiting program{RESET}")
                                sys.exit()
                            else: #Default to trying again even on invalid input
                                continue #Restart'try different names' loop
                    else:
                        #New name is valid and doesn't exist
                        db_path = new_db_path
                        break #Exit 'try different names' loop
                break #Exit main menu loop

            elif choice == '3':
                #Exit the program
                print(f"{INFO}Exiting program{RESET}")
                sys.exit()
            
            else:
                print(f"{INFO}Invalid choice. Please enter 1, 2, or 3{RESET}")
    else:
        #Step 2: When the default database does NOT exist
        while True:
            user_choice_create = input(f"{INFO}Database directory {default_db_path} doesn't exist. Do you want to create it?{RESET} (yes/no): ").lower()
            if user_choice_create in ['yes', 'y']:
                #Default name or a custom one
                while True:
                    user_choice_db_name = input(f"Do you want to use the default database path {default_db_path}? (yes/no): ").lower()
                    if user_choice_db_name in ['yes', 'y']:
                        db_path = default_db_path
                        break # from db name choice loop
                    elif user_choice_db_name in ['no', 'n']:
                        #Use for custom database name
                        while True: #Loop to allow user to try different names
                            new_db_path = input("\nEnter your desired database path (directory name): ")
                            if not new_db_path:
                                print(f"{INFO}Database path cannot be empty{RESET}")
                                continue
                            
                            if os.path.isdir(new_db_path):
                                print(f"\n{WARNING}Warning: A database directory named {new_db_path} already exists{RESET}")
                                overwrite_choice = input("Do you want to overwrite it? (yes/no): ").lower()
                                if overwrite_choice in ['yes', 'y']:
                                    try:
                                        print(f"{INFO}Deleting existing database directory {new_db_path}...{RESET}")
                                        shutil.rmtree(new_db_path)
                                        print(f"{SUCCESS}Deletion successful{RESET}")
                                        db_path = new_db_path
                                        break # from 'try different names' loop
                                    except Exception as e:
                                        print(f"{WARNING}Error deleting directory: {e}{RESET}")
                                        sys.exit()
                                else:
                                    print("Please choose an option:")
                                    print("  [ 1 ] Try another name")
                                    print("  [ 2 ] Exit the program")
                                    exit_choice = input("Enter your choice (1 or 2): ")
                                    if exit_choice == '2':
                                        print(f"{INFO}Exiting program{RESET}")
                                        sys.exit()
                                    else: # Default to try again
                                        continue # to start of 'try different names' loop
                            else:
                                db_path = new_db_path
                                break # from 'try different names' loop
                        break # from db name choice loop
                    else:
                        print(f"{INFO}Invalid input. Please enter 'yes' or 'no'{RESET}")
                break # Exit the creation confirmation loop
            elif user_choice_create in ['no', 'n']:
                print(f"{INFO}Exiting database creation{RESET}")
                sys.exit()
            else:
                print(f"{WARNING}Invalid input. Please enter 'yes' or 'no'{RESET}")


    #Step 3: Collection name
    while True:
        user_choice_collection_name = input(f"\nDo you want to use the default collection name {default_collection_name}? (yes/no): ").lower()
        if user_choice_collection_name in ['yes', 'y']:
            collection_name = default_collection_name
            break
        elif user_choice_collection_name in ['no', 'n']:
            new_collection_name = input("Enter your desired collection name: ")
            if new_collection_name:
                collection_name = new_collection_name
                break
            else:
                print(f"{WARNING}Collection name cannot be empty{RESET}")
        else:
            print(f"{WARNING}Invalid input. Please enter 'yes' or 'no'{RESET}")


    #Step 4: Create the database and collection
    try:
        print(f"\n{INFO}Creating database in directory: {db_path}...{RESET}")
        client = chromadb.PersistentClient(path=db_path)

        print(f"{INFO}Creating collection: {collection_name}...{RESET}")
        collection = client.get_or_create_collection(name=collection_name)

        print("\n----------------------------------------------------")
        print(f"{SUCCESS}Success!{RESET}")
        print(f"{INFO}Database path '{db_path}' is ready{RESET}")
        print(f"Collection {collection.name} has been created inside {db_path}")
        print("----------------------------------------------------")

    except Exception as e:
        print(f"\n{WARNING}An error occurred during database creation: {e}{RESET}")
        sys.exit()


if __name__ == "__main__":
    create_chroma_db()
    print(f"\n{INFO}Program finished{RESET}")
