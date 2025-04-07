import os
import json
from typing import List


def file_matches_criteria(data, target_url, target_path, param_value):
    """
    Checks if the given OpenAPI JSON data matches:
      1. Has at least one server whose URL == target_url.
      2. Has a path == target_path.
      3. Under that path (assuming a 'post' operation),
         the requestBody's 'method' property default == param_value.
    """
    # 1) Check servers
    servers = data.get("servers", [])
    if not any(s.get("url") == target_url for s in servers):
        return False

    # 2) Check for target_path in "paths"
    paths = data.get("paths", {})
    if target_path not in paths:
        return False

    # 3) Look for a 'post' operation under that path
    operation_data = paths[target_path].get("post")
    if not operation_data:
        return False

    # 4) Check "method" default in requestBody -> content -> application/json -> schema -> properties -> method
    request_body = operation_data.get("requestBody", {})
    content = request_body.get("content", {})
    app_json = content.get("application/json", {})
    schema = app_json.get("schema", {})
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
) -> List[str]:
    """
    Recursively searches `folder_path` for JSON files.
    For each file:
      - Parses as JSON
      - Checks if it matches the criteria:
        (server == target_url, path == target_path, method.default == param_value)
      - If so, copies the content into a new file under `output_folder`,
        named with `param_value` (appended by an index if multiple matches).

    Returns a list of matched file paths.
    """
    matching_files = []
    file_counter = 0  # to handle multiple matches

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
                    # Not valid JSON, skip
                    continue

                if file_matches_criteria(data, target_url, target_path, param_value):
                    matching_files.append(full_path)

                    # Generate a new filename in case multiple files match
                    new_filename = param_value
                    # If multiple matches, append an index: param_value_1.json, param_value_2.json, etc.
                    if file_counter > 0:
                        new_filename += f"_{file_counter}"
                    new_filename += ".json"

                    new_full_path = os.path.join(output_folder, new_filename)

                    # Write the matched JSON data to the new file
                    with open(new_full_path, "w", encoding="utf-8") as out_f:
                        json.dump(data, out_f, indent=2)

                    os.remove(full_path)  # Remove the original file

                    file_counter += 1

    return matching_files


if __name__ == "__main__":
    # Example usage
    folder_to_search = "openAPI"  # where we look for existing JSON files

    # The three criteria
    target_url = "https://base-mainnet.core.chainstack.com"
    target_path = "/2fc1de7f08c0465f6a28e3c355e0cb14"

    param_values = [
        "eth_blockNumber",
        "eth_getBlockByHash",
        "eth_getBlockByNumber",
        "eth_getBlockTransactionCountByHash",
        "eth_getBlockTransactionCountByNumber",
        "eth_getUncleCountByBlockHash",
        "eth_getUncleCountByBlockNumber",
        "eth_getUncleByBlockNumberAndIndex",
        "eth_getUncleByBlockHashAndIndex",
        "eth_getBlockReceipts",
        "eth_chainId",
        "eth_syncing",
        "eth_call",
        "eth_callMany",
        "eth_estimateGas",
        "eth_createAccessList",
        "eth_gasPrice",
        "eth_feeHistory",
        "eth_newFilter",
        "eth_newBlockFilter",
        "eth_uninstallFilter",
        "eth_getFilterChanges",
        "eth_getFilterLogs",
        "eth_getLogs",
        "eth_accounts",
        "eth_getBalance",
        "eth_getStorageAt",
        "eth_getTransactionCount",
        "eth_getCode",
        "eth_getProof",
        "eth_getTransactionByHash",
        "eth_getRawTransactionByHash",
        "eth_getTransactionByBlockHashAndIndex",
        "eth_getRawTransactionByBlockHashAndIndex",
        "eth_getTransactionByBlockNumberAndIndex",
        "eth_getRawTransactionByBlockNumberAndIndex",
        "eth_getTransactionReceipt",
        "eth_maxPriorityFeePerGas",
        "eth_sendRawTransaction",
        "eth_newPendingTransactionFilter",
        "web3_clientVersion",
        "eth_protocolVersion",
        "web3_sha3",
        "net_listening",
        "debug_getModifiedAccountsByNumber",
        "debug_getModifiedAccountsByHash",
        "debug_storageRangeAt",
        "debug_traceBlockByHash",
        "debug_traceBlockByNumber",
        "debug_traceTransaction",
        "debug_traceCall",
        "debug_traceCallMany",
        "trace_call",
        "trace_callMany method",
        "trace_replayBlockTransactions",
        "trace_replayTransaction",
        "trace_transaction",
        "trace_get",
        "trace_block",
    ]

    folder_name = "client_info"

    output_folder = f"fixed/bnb_node_api"

    failed_for = []

    for param_value in param_values:
        # Call the function to find matching files
        results = find_matching_files(
            folder_to_search, target_url, target_path, param_value, output_folder
        )

        if results:
            print("Files matching criteria:")
            for path in results:
                print("  ", path)
        else:
            failed_for.append(param_value)

    if len(failed_for) > 0:
        print("\n\nFailed finding following files:\n", failed_for)
