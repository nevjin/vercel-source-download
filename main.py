import requests
import os
import base64
import json
from urllib.parse import quote, urlparse, parse_qs, urlencode, urlunparse

VERCEL_TOKEN = "VERCEL_TOKEN"

DEPLOYMENT_UID = "DEPLOYMENT_UID"
LIVE_URL = "LIVE_URL"
TEAM_ID = "TEAM_ID"

OUTPUT_DIR = "OUTPUT_DIRECTORY"

HEADERS = {
    "Authorization": f"Bearer {VERCEL_TOKEN}"
}

def get_file_tree(base_path=""):

    encoded_base_path = base_path.replace("\\", "/")

    url = f"https://vercel.com/api/file-tree/{LIVE_URL}?base=src/{encoded_base_path}&teamId={TEAM_ID}"

    print(f"Fetching file tree for: {url}")
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching file tree for base path '{base_path}': {e}")
        return [] 

def download_file_content(file_link, local_file_path):
    parsed_url = urlparse(file_link)
    query_params = parse_qs(parsed_url.query)
    query_params['teamId'] = [TEAM_ID] 
    new_query = urlencode(query_params, doseq=True)
    final_file_url = urlunparse(parsed_url._replace(query=new_query))

    print(f"Downloading file from: {final_file_url}")
    try:
        response = requests.get(final_file_url, headers=HEADERS)
        response.raise_for_status() 

        data = response.json().get("data")
        if data:
            decoded_content = base64.b64decode(data) 

            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

            with open(local_file_path, "wb") as f:
                f.write(decoded_content)
            print(f"Saved: {local_file_path}")
        else:
            print(f"No content data found for {final_file_url}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file '{local_file_path}' from '{final_file_url}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred while processing '{local_file_path}': {e}")

def traverse_and_download(items, current_local_path):
    os.makedirs(current_local_path, exist_ok=True)

    for item in items:
        item_name = item["name"]
        item_type = item["type"]

        full_local_path = os.path.join(current_local_path, item_name)

        if item_type == "directory":
            print(f"Entering directory: {item_name} (local path: {full_local_path})")

            if current_local_path == OUTPUT_DIR:

                relative_path_for_api = item_name
            else:

                relative_path_for_api = os.path.relpath(full_local_path, OUTPUT_DIR)

            print(f"  API base_path for next level: {relative_path_for_api}")

            next_tree_items = get_file_tree(relative_path_for_api)

            if not next_tree_items:
                print(f"  No items found for directory '{relative_path_for_api}' on Vercel API. It might be empty or inaccessible.")

            traverse_and_download(next_tree_items, full_local_path)
        elif item_type == "file":

            file_link = item["link"]
            download_file_content(file_link, full_local_path)

def main():
    print(f"Starting Vercel source code download to: {OUTPUT_DIR}")

    initial_tree = get_file_tree(base_path="")

    if initial_tree:

        traverse_and_download(initial_tree, OUTPUT_DIR)
        print("\nDownload complete! All files have been saved locally.")
    else:
        print("\nFailed to retrieve initial file tree. Aborting download.")

if __name__ == "__main__":
    main()