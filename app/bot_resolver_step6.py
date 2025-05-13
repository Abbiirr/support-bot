#!/usr/bin/env python3
import os
import re

# Regex to capture entire <log-row> block
LOG_ROW_BLOCK_PATTERN = re.compile(r'(<log-row>.*?</log-row>)', re.DOTALL | re.IGNORECASE)
# Pattern to identify the invocation log-message for deposit
INVOCATION_PATTERN = re.compile(
    r'Service Invocation returned:.*?Method:\s*doAccountBaseDeposit',
    re.DOTALL | re.IGNORECASE
)
# Regex to extract AuthRespCode from JSON inside a block
AUTH_PATTERN = re.compile(r'"AuthRespCode"\s*:\s*"(\d+)"')


def step6(request_id: str, log_file_path: str) -> str:
    """
    Step 6: Locate the log-row block for the given request_id,
    extract the AuthRespCode, and return a status message.

    Args:
        request_id: The request ID to filter blocks.
        log_file_path: Path to the decompressed .log file.

    Returns:
        A string indicating success if code==1, or an error message otherwise.
    """
    # Validate inputs
    if not os.path.isfile(log_file_path):
        raise FileNotFoundError(f"Log file not found: {log_file_path}")

    # Read the full log content
    with open(log_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract individual log-row blocks
    blocks = LOG_ROW_BLOCK_PATTERN.findall(content)

    # Search for the specific invocation block
    for block in blocks:
        if f'<request-id>{request_id}</request-id>' in block and INVOCATION_PATTERN.search(block):
            # Extract AuthRespCode
            m = AUTH_PATTERN.search(block)
            if m:
                code = m.group(1)
                if code == '1':
                    print(f"AuthRespCode=1 for request-id {request_id}: success")
                    return f"AuthRespCode=1 for request-id {request_id}: success"
                else:
                    print(f"AuthRespCode={code} for request-id {request_id}: this is the problem")
                    return f"AuthRespCode={code} for request-id {request_id}: this is the problem"

    # If no matching block found
    print(f"No invocation block with AuthRespCode found for request-id {request_id}")
    return f"No invocation block with AuthRespCode found for request-id {request_id}"