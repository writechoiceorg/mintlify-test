import os
import json
import re


def get_file_paths(folder_path):
    """
    Returns a list of full file paths for every file in 'folder_path'.
    """
    file_paths = []
    for item in os.listdir(folder_path):
        full_path = os.path.join(folder_path, item)
        if os.path.isfile(full_path):
            file_paths.append(full_path)
    return file_paths


def natural_sort_key(text):
    """
    Splits text into alphanumeric chunks and converts digit chunks to integers.
    Example:
        "doc2.txt" -> ["doc", 2, ".txt"]
        "doc10.txt" -> ["doc", 10, ".txt"]
    Sorting by these lists ensures numbers are sorted by value (2 < 10),
    rather than lexicographically ("10" < "2" if we just do ASCII sort).
    """

    def atoi(token):
        return int(token) if token.isdigit() else token.lower()

    return [atoi(chunk) for chunk in re.split(r"(\d+)", text)]


def main():
    folder_path = "doc"
    files_in_directory = get_file_paths(folder_path)

    # Sort the files by the numeric parts of their basenames
    # so 'doc2.txt' appears before 'doc10.txt', for example
    files_in_directory.sort(key=lambda path: natural_sort_key(os.path.basename(path)))

    print("Files found (sorted):")
    for file_path in files_in_directory:
        print(file_path)

    # Write the sorted list of file paths to a JSON file
    output_file = "files.json"
    with open(output_file, "w", encoding="utf-8") as json_out:
        json.dump(files_in_directory, json_out, indent=2, ensure_ascii=False)

    print(f"\nSorted file paths written to '{output_file}'")


if __name__ == "__main__":
    main()
