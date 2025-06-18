import subprocess
import sys

# --- Dependency List ---
REQUIRED_LIBS = [
    "chromadb", "requests", "beautifulsoup4", "PyMuPDF", "langchain", 
    "collections", "urllib", "os", "time", "uuid",
    "pathlib", "colorama"
]

def check_library(lib_name):
    # Uses importlib.metadata. Returns True if installed, False otherwise.
    # PyMuPDF is imported as 'fitz'
    if lib_name == "PyMuPDF":
        lib_name = "fitz"
    # beautifulsoup4 is imported as 'bs4'
    elif lib_name == "beautifulsoup4":
        lib_name = "bs4"
        
    try:
        __import__(lib_name)
        return True
    except ImportError:
        return False

def install_libraries(libs_to_install):
    if not libs_to_install:
        print("No libraries to install.")
        return

    print("\nAttempting to install missing libraries via pip. This will take a few mintues.")
    try:
        # Calling pip via subprocess
        for lib in libs_to_install:
            print(f"Installing {lib}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
        print("\nInstallation successful!")
    except subprocess.CalledProcessError as e:
        print(f"\nAn error occurred during installation: {e}")
        print("Please try installing the libraries manually.")
    except FileNotFoundError:
        print("\nError: 'pip' command not found.")
        print("Please ensure pip is installed and in your system's PATH.")


def main():
    # Check for dependencies and prompt for installation.
    all_libs = REQUIRED_LIBS
    installed_libs = []
    missing_libs = []

    print("Checking Project Dependencies")

    for lib in all_libs:
        if check_library(lib):
            installed_libs.append(lib)
        else:
            missing_libs.append(lib)

    # --- Report Status ---
    if installed_libs:
        print("\n[✔] The following libraries are already installed:")
        for lib in installed_libs:
            print(f"  - {lib}")
    
    if not missing_libs:
        print("\nAll required libraries are installed. You're all set!")
        return

    print("\n[!] The following libraries are missing:")
    for lib in missing_libs:
        # Check if the missing library is required for a clearer message
        status = "Required" if lib in REQUIRED_LIBS else "Optional"
        print(f"  - {lib} ({status})")

    # Prompt for Install
    try:
        prompt = input("\nDo you want to install the necessary libraries? (yes/no): ").lower().strip()
    except KeyboardInterrupt:
        print("\n\nExiting Installation.")
        return

    if prompt in ['yes', 'y']:
        install_libraries(missing_libs)
    elif prompt in ['no', 'n']:
        print("Exiting Installation.")
    else:
        print("Invalid choice. Exiting Installation.")


if __name__ == "__main__":
    main()
