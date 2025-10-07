# FPSLocker SaltySD Downloader

## Introduction
This is a Python script that automates the downloading and processing of FPSLocker configuration files. It is primarily designed for use in a GitHub Actions environment and is capable of automatically detecting download links on the FPSLocker-Warehouse page, downloading all configuration files, extracting the SaltySD directory, and repackaging it as SaltySD.zip.

## Features
- Automatically retrieves the latest FPSLocker configuration download links from the GitHub repository
- Downloads configuration files and verifies file integrity (using SHA256 hash values)
- Extracts downloaded ZIP files
- Extracts content from the SaltySD directory
- Repackages the SaltySD directory into SaltySD.zip
- Cleans up temporary files

## Dependencies
- Python 3 (standard library)
- requests
- beautifulsoup4
- zipfile (standard library)
- hashlib (standard library)

## Usage
1. Ensure all dependencies are installed
2. Run the script: `python FPSLocker_SaltySD_download.py`
3. After the script execution, a SaltySD.zip file will be generated in the current directory

## Workflow
1. Creates a temporary directory to store downloaded and extracted files
2. Retrieves the latest download link from the GitHub repository page
3. Downloads the ZIP file and calculates its hash for verification
4. Extracts the downloaded ZIP file
5. Locates the SaltySD directory
6. Repackages the SaltySD directory
7. Cleans up the temporary directory

## Return Values
- 0: Successfully executed
- 1: An error occurred during execution

## Notes
- The script operates using a temporary directory, which is automatically cleaned up after execution
- Saves the hash value of the previously downloaded file to detect updates
- Supports download progress display
- Includes detailed error handling and log output

## License
Please refer to the LICENSE file in the project for detailed licensing information.