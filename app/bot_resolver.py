import os
import re
import json
import lzma
from datetime import datetime

# Output folder name (relative to the context file)
BOT_RESOLVE_FOLDER_NAME = 'bot-resolve'

# Regex patterns for parsing context
REF_PATTERN     = re.compile(r'Ref\s*No\.?\s*:?\s*(.+)', re.IGNORECASE)
PROJECT_PATTERN = re.compile(r'Project\s*:?\s*(\S+)', re.IGNORECASE)
DT_PATTERN      = re.compile(r'Date/Time\s*:?\s*([0-9]{4}-[0-9]{2}-[0-9]{2}\s+[0-9]{2}:[0-9]{2}:[0-9]{2})', re.IGNORECASE)

# Date/time format for context file
DT_FORMAT = "%Y-%m-%d %H:%M:%S"

# Path to log-location configuration
LOG_CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'config', 'log-location.json')
)


def load_log_config(project, log_type):
    """
    Load the log-location.json and return the 'How to find' template for project & log_type.
    Template uses placeholders: {year}, {month}, {date}, {hour}
    """
    with open(LOG_CONFIG_PATH, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    for entry in cfg:
        if entry.get('Project') == project and entry.get('Log Type') == log_type:
            return entry.get('How to find')
    raise ValueError(f"No log configuration for project={project}, log_type={log_type}")


def parse_context(context_path):
    """
    Extract the Project, Ref No., and Date/Time from a ticket context file.
    Returns (project, ref_no, dt_str).
    """
    project = None
    ref_no  = None
    dt_str  = None
    with open(context_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if project is None:
                m_proj = PROJECT_PATTERN.match(line)
                if m_proj:
                    project = m_proj.group(1).strip()
                    continue
            m_ref = REF_PATTERN.match(line)
            if m_ref:
                ref_no = m_ref.group(1).strip()
                continue
            m_dt = DT_PATTERN.match(line)
            if m_dt:
                dt_str = m_dt.group(1).strip()
    if None in (project, ref_no, dt_str):
        raise ValueError(f"Unable to parse Project, Ref No, or Date/Time from {context_path}")
    return project, ref_no, dt_str


def step1_identify_hour(context_path):
    """
    Step 1: Identify the hour slice for the log file.
    Writes 'need log of <YYYY-MM-DD.HH>' to bot-resolve/{ticket_name}_step_1.txt.
    Returns (project, dt).
    """
    project, _, dt_str = parse_context(context_path)
    dt = datetime.strptime(dt_str, DT_FORMAT)
    log_hour = dt.strftime("%Y-%m-%d.%H")

    # Write step 1 output
    ctx_dir     = os.path.dirname(context_path)
    output_dir  = os.path.abspath(os.path.join(ctx_dir, os.pardir, BOT_RESOLVE_FOLDER_NAME))
    os.makedirs(output_dir, exist_ok=True)
    ticket_name = os.path.splitext(os.path.basename(context_path))[0]
    step1_file  = os.path.join(output_dir, f"{ticket_name}_step_1.txt")
    with open(step1_file, 'w', encoding='utf-8') as out:
        out.write(f"need log of {log_hour}")

    return project, dt


def step2_determine_log_file(context_path):
    """
    Step 2: Determine the exact log file path using dt from step1 and config template.
    Writes the full path to bot-resolve/{ticket_name}_step_2.txt.
    Returns the output file path and the concrete log path.
    """
    project, dt = step1_identify_hour(context_path)

    # Load template from config
    template = load_log_config(project, 'Integration')

    # Extract components
    year   = dt.strftime("%Y")
    month  = dt.strftime("%m")
    date   = dt.strftime("%d")
    hour   = dt.strftime("%H")

    # Format concrete path
    log_filepath = template.format(year=year, month=month, date=date, hour=hour)

    # Write step 2 output
    ctx_dir     = os.path.dirname(context_path)
    output_dir  = os.path.abspath(os.path.join(ctx_dir, os.pardir, BOT_RESOLVE_FOLDER_NAME))
    os.makedirs(output_dir, exist_ok=True)
    ticket_name = os.path.splitext(os.path.basename(context_path))[0]
    step2_file  = os.path.join(output_dir, f"{ticket_name}_step_2.txt")
    with open(step2_file, 'w', encoding='utf-8') as out:
        out.write(log_filepath)

    return log_filepath, step2_file


def step3_extract_log(context_path):
    """
    Step 3: Locate the xz archive under '../log-files', decompress it, and write the raw log.
    Writes decompressed content to bot-resolve/{ticket_name}_step_3.log.
    Returns the output log path.
    """
    # Get concrete path and path of step2 file
    log_filepath, _ = step2_determine_log_file(context_path)

    # Determine archive directory and file name
    ctx_dir      = os.path.dirname(context_path)
    archive_dir  = os.path.abspath(os.path.join(ctx_dir, os.pardir, 'log-files'))
    archive_name = os.path.basename(log_filepath)
    archive_path = os.path.join(archive_dir, archive_name)

    if not os.path.isfile(archive_path):
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    # Decompress the .xz archive
    with lzma.open(archive_path, 'rt', encoding='utf-8') as src:
        content = src.read()

    # Write decompressed log to step 3 file
    output_dir  = os.path.abspath(os.path.join(ctx_dir, os.pardir, BOT_RESOLVE_FOLDER_NAME))
    ticket_name = os.path.splitext(os.path.basename(context_path))[0]
    step3_file  = os.path.join(output_dir, f"{ticket_name}_step_3.log")
    with open(step3_file, 'w', encoding='utf-8') as out:
        out.write(content)

    return step3_file


def resolve_ticket(context_path, report_id=None):
    """
    Orchestrator: runs steps 1, 2, and 3 in sequence.
    Returns dict with paths for all step outputs.
    """
    project, dt               = step1_identify_hour(context_path)
    log_filepath, step2_path = step2_determine_log_file(context_path)
    step3_path               = step3_extract_log(context_path)
    ticket_name              = os.path.splitext(os.path.basename(context_path))[0]
    step1_path               = os.path.abspath(
        os.path.join(os.path.dirname(context_path), os.pardir,
                     BOT_RESOLVE_FOLDER_NAME, f"{ticket_name}_step_1.txt")
    )
    from bot_resolver_step4 import step4
    ref_no = parse_context(context_path)[1]

    output_path = step4(ref_no, step3_path)
    print("Step 4 output at:", output_path)
    return {
        'step_1_file': step1_path,
        'step_2_file': step2_path,
        'step_3_file': step3_path
    }
