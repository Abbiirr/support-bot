#!/usr/bin/env python3
import os
import re

# Output folder name (relative to context)
BOT_RESOLVE_FOLDER_NAME = 'bot-resolve'

# Regex to capture entire <log-row> block
LOG_ROW_BLOCK_PATTERN = re.compile(r'(<log-row>.*?</log-row>)', re.DOTALL | re.IGNORECASE)


def step5(request_id: str, log_file_path: str) -> str:
    """
    Step 5: Extract all <log-row> blocks matching the given request_id
    from the decompressed log file, writing them to
    bot-resolve/{ticket_name}_step_5.log

    Args:
        request_id: The specific request ID to filter log rows.
        log_file_path: Absolute path to the decompressed log file (.log).

    Returns:
        Path to the generated step_5 log snippet file.
    """
    # Validate inputs
    if not os.path.isfile(log_file_path):
        raise FileNotFoundError(f"Log file not found: {log_file_path}")

    # Read the full log content
    with open(log_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all log-row blocks
    blocks = LOG_ROW_BLOCK_PATTERN.findall(content)

    # Filter blocks containing the exact request-id tag
    needle = f'<request-id>{request_id}</request-id>'
    matching_blocks = [block for block in blocks if needle in block]

    # Prepare output path
    ticket_name = os.path.basename(log_file_path).replace('_step_3.log', '')
    output_dir = os.path.dirname(log_file_path)
    os.makedirs(output_dir, exist_ok=True)
    step5_file = os.path.join(output_dir, f"{ticket_name}_step_5.log")

    # Write results
    with open(step5_file, 'w', encoding='utf-8') as out:
        if matching_blocks:
            for block in matching_blocks:
                out.write(block + '\n')
        else:
            out.write(f"No log-row found for request-id {request_id}\n")
    from bot_resolver_step6 import step6

    step6_path = step6(request_id,
                       log_file_path)
    print("Step 6 output:", step6_path)

    return step5_file
