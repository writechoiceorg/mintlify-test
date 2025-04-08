import os
import json
from typing import List


def resolve_reference(ref: str, data: dict) -> dict:
    """
    Resolves a JSON pointer ($ref) from the provided OpenAPI data.
    Only supports local references (starting with "#/").
    For example, given a ref "#/components/schemas/JsonRpcRequestForL1ChainId",
    the function navigates the `data` dict accordingly.
    """
    if not ref.startswith("#/"):
        raise ValueError("External references are not supported: " + ref)
    parts = ref.lstrip("#/").split("/")
    ref_obj = data
    for part in parts:
        # If part is not found, return an empty dict
        ref_obj = ref_obj.get(part, {})
    return ref_obj


def resolve_schema(schema: dict, data: dict) -> dict:
    """
    Recursively resolves the schema if it has a $ref key.
    This function will replace the schema with the referenced schema
    until there is no more "$ref" to follow.
    """
    while "$ref" in schema:
        schema = resolve_reference(schema["$ref"], data)
    return schema


def file_matches_criteria(data, target_url, target_path, param_value):
    """
    Checks if the given OpenAPI JSON data matches:
      1. At least one server with URL == target_url.
      2. Contains the target_path in the 'paths' section.
      3. Under that path's 'post' operation, the requestBody's schema has a 'method'
         property with default value == param_value. The schema may use $ref to define the body.
    """
    # 1) Check for the target server URL
    servers = data.get("servers", [])
    if not any(s.get("url") == target_url for s in servers):
        return False

    # 2) Check if the target_path exists in "paths"
    paths = data.get("paths", {})
    if target_path not in paths:
        return False

    # 3) Look for a 'post' operation under the target path
    operation_data = paths[target_path].get("post")
    if not operation_data:
        return False

    # 4) Retrieve the schema for the requestBody (application/json)
    request_body = operation_data.get("requestBody", {})
    content = request_body.get("content", {})
    app_json = content.get("application/json", {})
    schema = app_json.get("schema", {})

    # 5) Resolve the schema if it contains a $ref (it might be under components)
    if "$ref" in schema:
        schema = resolve_schema(schema, data)

    # 6) Now check the "method" property in the schema's properties
    properties = schema.get("properties", {})
    method_prop = properties.get("method", {})
    default_val = method_prop.get("default")

    return default_val == param_value


def find_matching_files(
    folder_path: str,
    target_url: str,
    target_path: str,
    param_value: str,
    output_folder: str,
    remove_files=False,
) -> List[str]:
    """
    Recursively searches `folder_path` for JSON files.
    For each file:
      - Parses as JSON.
      - Checks if it matches the criteria (server URL, path, and method.default).
      - If so, copies the content to a new file under `output_folder` with a name based on param_value.
      - Deletes the original file.
    Returns a list of matched file paths.
    """
    matching_files = []
    file_counter = 0  # to handle multiple matching files

    # Ensure output_folder exists
    os.makedirs(output_folder, exist_ok=True)

    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename.lower().endswith(".json"):
                full_path = os.path.join(root, filename)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Skip invalid JSON files
                    continue

                # Check if the file matches the criteria
                if file_matches_criteria(data, target_url, target_path, param_value):
                    matching_files.append(full_path)

                    # Create a new filename based on param_value (append an index if needed)
                    new_filename = param_value
                    if file_counter > 0:
                        new_filename += f"_{file_counter}"
                    new_filename += ".json"

                    new_full_path = os.path.join(output_folder, new_filename)

                    # Write the matched JSON data to the new file
                    with open(new_full_path, "w", encoding="utf-8") as out_f:
                        json.dump(data, out_f, indent=2)

                    if remove_files is True:
                        # Remove the original file
                        os.remove(full_path)

                    file_counter += 1

    return matching_files


if __name__ == "__main__":
    # Example usage
    folder_to_search = "openAPI"  # folder containing JSON files

    # The criteria
    target_url = "https://nd-326-444-187.p2pify.com"
    target_path = "/9de47db917d4f69168e3fed02217d15b"

    param_values = [
        "getAccountInfo",
        "getBalance",
        "getBlockHeight",
        "getBlock",
        "getBlockProduction",
        "getBlockCommitment",
        "getBlocks",
        "getBlocksWithLimit",
        "getBlockTime",
        "getClusterNodes",
        "getEpochInfo",
        "getEpochSchedule",
        "getFeeForMessage",
        "getFirstAvailableBlock",
        "getGenesisHash",
        "getHighestSnapshotSlot",
        "getIdentity",
        "getInflationGovernor",
        "getInflationRate",
        "getInflationReward",
        "getLatestBlockhash",
        "getLeaderSchedule",
        "getMaxRetransmitSlot",
        "getMaxShredInsertSlot",
        "getMinimumBalanceForRentExemption",
        "getMultipleAccounts",
        "getProgramAccounts",
        "getRecentBlockhash",
        "getRecentPerformanceSamples",
        "getRecentPrioritizationFees",
        "getSignaturesForAddress",
        "getSignatureStatuses",
        "getSlot",
        "getSlotLeader",
        "getStakeActivation",
        "getStakeMinimumDelegation",
        "getSupply",
        "getTokenAccountBalance",
        "getTokenAccountsByOwner",
        "getTokenLargestAccounts",
        "getLargestAccounts",
        "getTransaction",
        "isBlockhashValid",
        "simulateTransaction",
    ]

    # Example folder mapping (you can choose the one you need)
    folders = {
        1: "blocks_info",
        2: "transaction_info",
        3: "execute_transactions",
        4: "debug_and_trace",
        5: "chain_info",
        6: "gas_data",
        7: "accounts_info",
        8: "logs_and_events",
        9: "filter_handling",
        10: "client_info",
    }
    folder_name = folders[1]

    output_folder = f"fixed/solana_node_api"

    failed_for = []

    removing_files = True

    for param_value in param_values:
        # Call the function to find matching files
        results = find_matching_files(
            folder_to_search,
            target_url,
            target_path,
            param_value,
            output_folder,
            remove_files=removing_files,
        )

        if results:
            print("Files matching criteria:")
            for path in results:
                print("  ", path)
        else:
            failed_for.append(param_value)

    if len(failed_for) > 0:
        print("\n\nFailed finding the following files:\n", failed_for)
    elif len(failed_for) == 0 and removing_files is False:
        print("\n\nAll files were found successfully.")
        for param_value in param_values:
            results = find_matching_files(
                folder_to_search,
                target_url,
                target_path,
                param_value,
                output_folder,
                remove_files=True,
            )
