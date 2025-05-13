import os
import re
from datetime import datetime

# Output folder name (relative to the context file)
BOT_RESOLVE_FOLDER_NAME = 'bot-resolve'

# Regex patterns for parsing context
REF_PATTERN = re.compile(r'Ref\s*No\.?\s*:?.*(.+)', re.IGNORECASE)
DT_PATTERN  = re.compile(r'Date/Time\s*:?\s*([0-9]{4}-[0-9]{2}-[0-9]{2}\s+[0-9]{2}:[0-9]{2}:[0-9]{2})', re.IGNORECASE)

# Date/time format for context file
DT_FORMAT = "%Y-%m-%d %H:%M:%S"

def parse_context(context_path):
    """
    Extract the Ref No. and Date/Time (YYYY-MM-DD HH:MM:SS) from a ticket context file.
    Returns (ref_no, dt_str).
    """
    ref_no = None
    dt_str = None
    with open(context_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            m_ref = REF_PATTERN.match(line)
            if m_ref:
                ref_no = m_ref.group(1).strip()
                continue
            m_dt = DT_PATTERN.match(line)
            if m_dt:
                dt_str = m_dt.group(1).strip()
    if not ref_no or not dt_str:
        raise ValueError(f"Unable to parse Ref No or Date/Time from {context_path}")
    return ref_no, dt_str

def resolve_ticket(context_path, report_id):
    """
    Reads the context file, builds the log-hour string for the correct hour,
    and writes a single-line request to bot-resolve/{ticket_name}_step_1.txt:
        need log of <YYYY-MM-DD.HH>
    """
    # Parse context
    ref_no, dt_str = parse_context(context_path)

    # Parse timestamp
    dt = datetime.strptime(dt_str, DT_FORMAT)

    # Build log-hour string
    log_hour = dt.strftime("%Y-%m-%d.%H")  # e.g. "2025-05-08.17"

    # Determine output path
    ctx_dir = os.path.dirname(context_path)
    output_dir = os.path.abspath(os.path.join(ctx_dir, os.pardir, BOT_RESOLVE_FOLDER_NAME))
    os.makedirs(output_dir, exist_ok=True)
    ticket_name = os.path.splitext(os.path.basename(context_path))[0]
    out_filename = f"{ticket_name}_step_1.txt"
    out_path = os.path.join(output_dir, out_filename)

    # Write the single-line request
    with open(out_path, 'w', encoding='utf-8') as out:
        out.write(f"need log of {log_hour}")

    # Optionally return the path
    return out_path
