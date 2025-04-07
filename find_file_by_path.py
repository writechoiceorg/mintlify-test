import os
import json


def find_operation_id(data: dict, path_part: str) -> str:
    """
    Looks for the first operationId in any standard HTTP method
    under the given path_part. Returns the operationId string if found,
    or None if no operationId is present.
    """
    path_data = data.get("paths", {}).get(path_part, {})
    possible_methods = ["get", "put", "post", "delete", "patch", "options", "head"]
    for method in possible_methods:
        method_data = path_data.get(method, {})
        operation_id = method_data.get("operationId")
        if operation_id is not None:
            return operation_id
    return None


def find_matching_files(folder_path: str, full_url: str, output_folder: str):
    """
    1. Recursively walk through 'folder_path'.
    2. For each .json file:
        a) Load as JSON.
        b) For each server in data['servers']:
           For each path in data['paths']:
               If server['url'] + path == full_url:
                   => MATCH
        c) If matched:
           - Extract operationId from the matching path.
           - Rename file to <operationId>.json or matched_<originalName>.json.
           - Copy to 'output_folder'.
           - Delete the original file.
    3. Return (matched_files, new_file_locations).
    """
    matched_files = []
    new_full_paths = []

    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename.lower().endswith(".json"):
                full_path = os.path.join(root, filename)

                # Attempt to parse JSON
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Not valid JSON; skip
                    continue

                # Check for a match: server_url + path_key == full_url
                servers = data.get("servers", [])
                paths = data.get("paths", {})
                path_that_matched = None

                for srv in servers:
                    srv_url = srv.get("url", "")
                    for path_key in paths:
                        # Combine the server URL & path
                        if srv_url + path_key == full_url:
                            path_that_matched = path_key
                            break
                    if path_that_matched:
                        break

                if path_that_matched is not None:
                    # We have a match; gather info for rename/move
                    matched_files.append(full_path)
                    operation_id = find_operation_id(data, path_that_matched)

                    if operation_id:
                        new_filename = f"{operation_id}.json"
                    else:
                        base_name, _ = os.path.splitext(filename)
                        new_filename = f"matched_{base_name}.json"

                    new_full_path = os.path.join(output_folder, new_filename)
                    new_full_paths.append(new_full_path)

                    # Write matched JSON data to new file
                    with open(new_full_path, "w", encoding="utf-8") as out_f:
                        json.dump(data, out_f, indent=2)

                    # Delete the original file
                    os.remove(full_path)

    return matched_files, new_full_paths


pathsv2 = [
    "getAddressInformation",
    "getExtendedAddressInformation",
    "getWalletInformation",
    "getTransactions",
    "getAddressBalance",
    "getAddressState",
    "packAddress",
    "unpackAddress",
    "getTokenData",
    "detectAddress",
    "getMasterchainInfo",
    "getMasterchainBlockSignatures",
    "getShardBlockProof",
    "getConsensusBlock",
    "lookupBlock",
    "shards",
    "getBlockTransactions",
    "getBlockTransactionsExt",
    "getBlockHeader",
    "tryLocateTx",
    "tryLocateResultTx",
    "tryLocateSourceTx",
    "getConfigParam",
    "runGetMethod",
]

pathsv3 = [
    "masterchainInfo",
    "blocks",
    "masterchainBlockShardState",
    "addressBook",
    "masterchainBlockShards",
    "transactions",
    "transactionsByMasterchainBlock",
    "transactionsByMessage",
    "adjacentTransactions",
    "messages",
    "nft/collections",
    "nft/items",
    "nft/transfers",
    "jetton/masters",
    "jetton/wallets",
    "jetton/transfers",
    "jetton/burns",
    "runGetMethod",
    "estimateFee",
    "account",
    "wallet",
]

if __name__ == "__main__":
    # Example usage
    folder_to_search = "openAPI"  # The folder containing .json files
    output_folder = "fixed/ton_node_api/v3"

    for path in pathsv3:
        full_url = f"https://ton-mainnet.core.chainstack.com/f2a2411bce1e54a2658f2710cd7969c3/api/v3/{path}"

        matched, renamed = find_matching_files(
            folder_to_search, full_url, output_folder
        )
        if matched:
            print("Matched & moved files:")
            for old, new in zip(matched, renamed):
                print("  ", old, "->", new)
        else:
            print("\n\nNo matches found for:", full_url, "\n\n")
