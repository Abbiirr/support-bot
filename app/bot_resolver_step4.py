# bot_resolver_step4.py
import os
import re

# Pattern to extract request-id from log-row blocks
REQUEST_ID_PATTERN = re.compile(r'<request-id>([^<]+)</request-id>', re.IGNORECASE)

# Output folder name (relative to context)
BOT_RESOLVE_FOLDER_NAME = 'bot-resolve'


def step4(ref_no: str, log_file_path: str) -> str:
    """
    Step 4: Search the decompressed log for <log-row> blocks containing ref_no,
    extract request-id from those blocks, and write results to
    bot-resolve/{ticket_name}_step_4.txt.

    Args:
        ref_no: The reference number or ExtId to search for in the log.
        log_file_path: Absolute path to the decompressed log file (.log).

    Returns:
        Path to the generated step_4 output file.
    """
    # Ensure log exists
    if not os.path.isfile(log_file_path):
        raise FileNotFoundError(f"Log file not found: {log_file_path}")

    # Read entire log content
    with open(log_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all <log-row>...</log-row> blocks
    blocks = re.findall(r'<log-row>(.*?)</log-row>', content, re.DOTALL | re.IGNORECASE)

    # Collect found request IDs where ref_no appears in the block
    found_ids = set()
    for block in blocks:
        if ref_no in block:
            m = REQUEST_ID_PATTERN.search(block)
            if m:
                found_ids.add(m.group(1))

    # Determine ticket name and output path
    ticket_name = os.path.basename(log_file_path).replace('_step_3.log', '')
    output_dir = os.path.dirname(log_file_path)
    os.makedirs(output_dir, exist_ok=True)
    step4_file = os.path.join(output_dir, f"{ticket_name}_step_4.txt")

    # Write results
    with open(step4_file, 'w', encoding='utf-8') as out:
        if found_ids:
            for rid in sorted(found_ids):
                out.write(rid + "\n")
        else:
            out.write(f"No request-id found for ref {ref_no}\n")

    return step4_file
