import os
import json
from collections import defaultdict

current_folder = "base_node_api"


def generate_mdx_and_reports(input_folder="fixed", output_folder="api-reference"):
    """
    1. Recursively finds .json in `input_folder`.
    2. For each file:
       - Parse OpenAPI data.
       - Extract first server, first path, first method, summary.
       - Generate an .mdx file in `output_folder` (mirroring folder structure).
         With front matter:
             ---
             title: "..."
             openapi: "openapi-file-path METHOD /endpoint"
             ---
         (No server included in 'openapi' line)
    3. Gathers each .mdx file path (minus extension) by subfolder => "report.json".
    4. Gathers all .json file paths (relative to `input_folder`) => "openapi.json".
    """

    os.makedirs(output_folder, exist_ok=True)

    # Dictionary: group_name -> list of doc paths (for final report)
    groups_dict = defaultdict(list)

    # List of all relative json paths found in input_folder
    json_paths = []

    # Typical HTTP methods in OpenAPI
    possible_methods = ["get", "put", "post", "delete", "patch", "options", "head"]

    for root, dirs, files in os.walk(f"{input_folder}/{current_folder}"):
        for filename in files:
            if filename.lower().endswith(".json"):
                # Relative path of the JSON file (for openapi.json and the front matter)
                rel_json_path = os.path.relpath(
                    os.path.join(root, filename), input_folder
                )
                json_paths.append(f"/openapi/{rel_json_path}")

                full_path = os.path.join(root, filename)

                # Parse JSON
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    print(f"[SKIP] Invalid JSON: {full_path}")
                    continue

                servers = data.get("servers", [])
                paths = data.get("paths", {})

                # Some basic validations
                if not servers:
                    print(f"[SKIP] No 'servers' in: {full_path}")
                    continue
                if not paths:
                    print(f"[SKIP] No 'paths' in: {full_path}")
                    continue

                # 1) Take the first server (not actually used in 'openapi:' line, but check we have it)
                server_url = servers[0].get("url", "")

                # 2) Take the first path key
                path_keys = list(paths.keys())
                path_key = path_keys[0]

                # 3) Find the first valid operation
                path_data = paths[path_key]
                chosen_method = None
                summary = "Untitled Endpoint"

                for method in possible_methods:
                    if method in path_data:
                        operation_data = path_data[method]
                        summary = operation_data.get("summary", summary)
                        chosen_method = method.upper()
                        break

                if not chosen_method:
                    print(f"[SKIP] No valid HTTP operation in: {full_path}")
                    continue

                # Build MDX front matter
                # Instead of 'api:', we now do 'openapi:' with JSON-file-path + METHOD + path
                mdx_content = f"""---
title: "{summary}"
openapi: "/openapi/{rel_json_path} {chosen_method} {path_key}"
---
"""

                # Mirroring the folder structure
                rel_dir = os.path.relpath(
                    root, input_folder
                )  # subfolders below 'fixed'
                out_dir = os.path.join(output_folder, rel_dir)
                os.makedirs(out_dir, exist_ok=True)

                base_name, _ = os.path.splitext(filename)
                mdx_filename = base_name + ".mdx"
                mdx_full_path = os.path.join(out_dir, mdx_filename)

                with open(mdx_full_path, "w", encoding="utf-8") as mdx_file:
                    mdx_file.write(mdx_content)

                print(f"[OK] Created MDX: {mdx_full_path}")

                # Build doc path (minus .mdx) => for "report.json"
                rel_out_dir = os.path.relpath(out_dir, output_folder)
                if rel_out_dir == ".":
                    # means no subfolder
                    group_name = "root"
                    doc_path_no_ext = os.path.join(
                        f"api-reference/{current_folder}", base_name
                    )
                else:
                    group_name = rel_out_dir.replace("\\", "/")
                    doc_path_no_ext = os.path.join(
                        "api-reference", group_name, base_name
                    )

                doc_path_no_ext = doc_path_no_ext.replace("\\", "/")
                groups_dict[group_name].append(doc_path_no_ext)

    # Create "report.json": array of { "group": "...", "pages": [...] }
    report_data = []
    for group_name in sorted(groups_dict.keys()):
        pages_list = groups_dict[group_name]
        report_data.append({"group": group_name, "pages": pages_list})

    report_path = os.path.join(output_folder, "report.json")
    with open(report_path, "w", encoding="utf-8") as rep:
        json.dump(report_data, rep, indent=2)
    print(f"[OK] report.json created at: {report_path}")

    # Create "openapi.json": array of all .json file paths relative to input_folder
    openapi_path = os.path.join(output_folder, "openapi.json")
    with open(openapi_path, "w", encoding="utf-8") as rep:
        json.dump(json_paths, rep, indent=2)
    print(f"[OK] openapi.json created at: {openapi_path}")


if __name__ == "__main__":
    generate_mdx_and_reports()
