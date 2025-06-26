import sys
import subprocess
import importlib.util

def bootstrap_dependencies():
    #Checks for core dependencies. The script must be re-run after installation.

    core_libs = {
        "requests": "requests",
        "packaging": "packaging",
        "colorama": "colorama"
    }

    missing_libs = []

    print("Checking for core script dependencies...")
    for lib_name, package_name in core_libs.items():
        spec = importlib.util.find_spec(lib_name)
        if spec is None:
            missing_libs.append(package_name)

    if missing_libs:
        print(f"\n[ ! ] The following core dependencies are missing: {', '.join(missing_libs)}")
        print("Attempting to install them via pip...")

        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_libs])
            print(f"\n ✔ Core dependencies installed successfully")
            print("[ ! ] Please run the script again to continue")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"\n ❌ EROR: Failed to install core dependencies: {e}")
            print(f"Please install them manually by running: pip install {' '.join(missing_libs)}")
        
        sys.exit()
    else:
        print(f"All core dependencies are present")


# SCRIPT EXECUTION STARTS HERE
# 1. Run the bootstrap check immediately. If it finds missing libraries it will install them and exit
bootstrap_dependencies()

# 2. If the script continues past this, core dependencies are installed and will be imported
import requests
from packaging.version import parse as parse_version
import importlib.metadata
import colorama
from colorama import Fore, Style


# 3. Initialize Colorama and define colors
colorama.init(autoreset=True)
HEADING = Fore.YELLOW
SUCCESS = Fore.GREEN
WARNING = Fore.RED
INFO = Fore.CYAN

# Dependency List installed/updated via pip
REQUIRED_LIBS = [
    "chromadb", "requests", "beautifulsoup4", "PyMuPDF", "langchain",
    "colorama", "packaging"
]


def get_latest_version(package_name):
    # Fetches the latest version from PyPI, returns the version string or None if not found or an error occurs.
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        data = response.json()
        return data['info']['version']
    except requests.exceptions.RequestException as e:
        print(f"{WARNING}Could not fetch version for {package_name} {e}")
        return None


def update_libraries(libs_to_update):
    # Use pip to install or upgrade a list of libraries.
    if not libs_to_update:
        print(f"{INFO}No libraries selected for update")
        return

    print(f"\n{INFO}Attempting to update libraries via pip...")
    try:
        # Calling pip via subprocess with the --upgrade flag
        for lib in libs_to_update:
            print(f"{INFO}Updating {lib}...")
            # Use --upgrade to ensure the package is updated to the latest version
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--upgrade", lib]
            )
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n{WARNING}An error occurred during updates: {e}")
        print("Please try updating the libraries manually")
        return False
    except FileNotFoundError:
        print(f"\n{WARNING}EROR: 'pip' command not found")
        print("Please ensure pip is installed and in your system's PATH")
        return False


def install_missing_libraries(libs_to_install):
    # Use pip to install a list of missing libraries.
    if not libs_to_install:
        print("No missing libraries to install")
        return

    print(f"\n{INFO}Attempting to install missing libraries via pip...")
    try:
        for lib in libs_to_install:
            print(f"Installing {lib}...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", lib]
            )
        print(f"\n{SUCCESS}Installation of missing libraries successful\n")
    except subprocess.CalledProcessError as e:
        print(f"\n{WARNING}An error occurred during installation: {e}")
        print("Please try installing the libraries manually")
    except FileNotFoundError:
        print(f"\n{WARNING}Error: 'pip' command not found")
        print("Please ensure pip is installed and in your system's PATH.")


def main():
    # Checks for dependencies, identifies missing or outdated packages, prompts user for installation or updates
    missing_libs = []
    outdated_libs = []
    uptodate_libs = []

    print("\nChecking Project Dependencies...")

    for lib in REQUIRED_LIBS:
        try:
            installed_version = importlib.metadata.version(lib)
            latest_version = get_latest_version(lib)

            if latest_version and parse_version(installed_version) < parse_version(latest_version):
                outdated_libs.append({
                    "name": lib,
                    "installed": installed_version,
                    "latest": latest_version
                })
            else:
                uptodate_libs.append({"name": lib, "version": installed_version})
        except importlib.metadata.PackageNotFoundError:
            missing_libs.append(lib)

    # --- Report Status ---
    if uptodate_libs:
        print(f"\n ✔ {HEADING} The following libraries are installed and up-to-date:")
        for lib in uptodate_libs:
            print(f"  - {lib['name']} (v{lib['version']})")

    if not missing_libs and not outdated_libs:
        print("\nAll required libraries are installed and up-to-date")
        return

    if missing_libs:
        print(f"\n{HEADING} ❌ The following required libraries are missing:")
        for lib in missing_libs:
            print(f"  - {lib}")
        try:
            prompt = input("\nDo you want to install them? (yes/no): ").lower().strip()
            if prompt in ['yes', 'y']:
                install_missing_libraries(missing_libs)
            else:
                print(f"\n{WARNING}Skipping installation of missing libraries. The program may not run correctly\n")
        except KeyboardInterrupt:
            print("\n\nExiting Installation")
            return

    if outdated_libs:
        print(f"\n{HEADING} The following libraries are installed but outdated:")
        for lib in outdated_libs:
            print(f"  - {lib['name']} (Installed: v{lib['installed']}, Latest: v{lib['latest']})")

        # --- Prompt for Update ---
        try:
            print(f"\n{HEADING}How would you like to proceed with updates?")
            print(" [ 1 ] Update all outdated libraries")
            print(" [ 2 ] Choose which libraries to update")
            print(" [ 3 ] Don't update any libraries")
            choice = input(f"{INFO}Enter your choice (1/2/3): ").strip()

            if choice == '1':
                libs_to_update_all = [lib['name'] for lib in outdated_libs]
                if update_libraries(libs_to_update_all):
                    print(f"\n{SUCCESS}All needed libraries have been updated to the current available version")
                print("Exiting.")

            elif choice == '2':
                for lib in outdated_libs:
                    prompt = input(f"  Update {INFO}{lib['name']} from v{lib['installed']} to v{lib['latest']}? (yes/no): ").lower().strip()
                    if prompt in ['yes', 'y']:
                        if update_libraries([lib['name']]):
                             print(f"  > '{lib['name']}' updated.")
                print("\nAll installs and updates are complete")
                print("Exiting\n")

            elif choice == '3':
                print("\nExiting without updating\n")
            else:
                print("\nInvalid choice. Exiting without updating\n")

        except KeyboardInterrupt:
            print("\nExiting Installation\n")
            return


if __name__ == "__main__":
    main()
