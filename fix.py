import os
import json
from urllib.parse import urlsplit


def fix_openapi_json(data, search_url, new_path_value, original_path_value):
    """
    Given parsed JSON from an OpenAPI file, if:
      - There's exactly one server whose URL == search_url
      - The OpenAPI has exactly one path == "/"
    Then remove everything after the hostname in that single server's URL,
    and rename the "/" path to "/{new_path_value}".

    Returns (modified_data, changed):
      - modified_data: the updated data (dict)
      - changed: True if the data was modified, otherwise False
    """
    servers = data.get("servers", [])
    paths = data.get("paths", {})

    # We want exactly one server, and that server's URL must match search_url exactly
    if len(servers) == 1 and servers[0].get("url") == search_url:
        # We also want exactly one path, and that path is "/"
        if len(paths) == 1 and original_path_value in paths:
            # Parse the search_url (e.g., "https://host.com/path1/path2")
            parsed = urlsplit(search_url)
            # Build just scheme + netloc, e.g. "https://host.com"
            new_domain = f"{parsed.scheme}://{parsed.netloc}"

            # Overwrite the server's URL with just the scheme://netloc portion
            servers[0]["url"] = new_domain

            # Rename the "/" path to "/{new_path_value}"
            paths[f"/{new_path_value}"] = paths.pop(original_path_value)

            return data, True

    return data, False


def find_and_fix_json(folder_path, search_url, new_path_value, original_path_value):
    """
    1. Searches the given folder (recursively) for *.json files.
    2. For each file, tries to load it as JSON.
    3. If it contains exactly one server with url == search_url, and exactly one path "/", fix it:
       - Server URL becomes scheme://netloc
       - "/" path is renamed to "/{new_path_value}"
    4. Saves the JSON back to the file if modified.

    Returns a list of updated file paths for reporting.
    """
    updated_files = []

    for root, dirs, files in os.walk(folder_path):

        for file_name in files:
            if file_name.lower().endswith(".json"):
                file_path = os.path.join(root, file_name)

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Not valid JSON, skip
                    continue

                # Attempt to fix the JSON
                modified_data, changed = fix_openapi_json(
                    data, search_url, new_path_value, original_path_value
                )

                if changed:
                    # Overwrite the file with changes
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(modified_data, f, indent=2)
                    updated_files.append(file_path)

    return updated_files


if __name__ == "__main__":
    # Example usage:
    folder_to_search = "openAPI"
    folder_to_search2 = "openAPI_backup"

    # For example, something like:
    search_url = "https://nd-326-444-187.p2pify.com/9de47db917d4f69168e3fed02217d15b"
    original_path_value = "/"
    new_path_value = f"9de47db917d4f69168e3fed02217d15b{original_path_value}".rstrip(
        "/"
    )

    results = find_and_fix_json(
        folder_to_search, search_url, new_path_value, original_path_value
    )

    find_and_fix_json(
        folder_to_search2, search_url, new_path_value, original_path_value
    )
    print("Updated files:")
    for f in results:
        print(f)
