import os
import json
import re
from datetime import datetime

# Folder names (relative to the context file)
REPORT_FOLDER_NAME = 'reports'
RESULT_FOLDER_NAME = 'kb-search-result'

# Regex patterns for parsing context
REF_PATTERN = re.compile(r'Ref\s*No\.?\s*:?\s*(.+)', re.IGNORECASE)
DT_PATTERN = re.compile(r'Date/Time\s*:?\s*(.+)', re.IGNORECASE)

# Date/time format for context file
DT_FORMAT = "%Y-%m-%d %H:%M:%S"


def parse_context(context_path):
    """
    Extract the Ref No. and Date/Time (YYYY-MM-DD HH:MM:SS) from a ticket context file.
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
                parts = m_dt.group(1).strip().split()
                if len(parts) >= 2:
                    dt_str = ' '.join(parts[0:2])
    if not ref_no or not dt_str:
        raise ValueError(f"Unable to parse Ref No or Date/Time from {context_path}")
    return ref_no, dt_str


def load_reports(report_dir):
    """
    Load all JSON files from the given reports directory.
    Returns a dict of { filename: parsed_json }.
    """
    reports = {}
    if not os.path.isdir(report_dir):
        return reports
    for fn in os.listdir(report_dir):
        if fn.lower().endswith('.json'):
            path = os.path.join(report_dir, fn)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    reports[fn] = json.load(f)
            except Exception:
                continue
    return reports


def find_best_match(ref_no, dt_str, report_dir):
    """
    Return the filename of the best-matching report in report_dir.
    First tries exact metadata.extId match; if none, falls back to nearest occurrence_datetime.
    """
    reports = load_reports(report_dir)
    # 1) Exact extId match
    for fn, rpt in reports.items():
        meta = rpt.get('metadata', {})
        if meta.get('extId') == ref_no:
            return fn
    # 2) Fallback: match by nearest occurrence_datetime
    closest_fn = None
    min_diff = None
    try:
        ctx_dt = datetime.strptime(dt_str, DT_FORMAT)
    except Exception:
        return None
    for fn, rpt in reports.items():
        meta = rpt.get('metadata', {})
        occ = meta.get('occurrence_datetime')
        if not occ:
            continue
        try:
            # Parse ISO8601 with offset
            rep_dt = datetime.fromisoformat(occ)
            # Convert to naive by dropping tzinfo
            rep_local = rep_dt.replace(tzinfo=None)
            diff = abs((rep_local - ctx_dt).total_seconds())
        except Exception:
            continue
        if min_diff is None or diff < min_diff:
            min_diff = diff
            closest_fn = fn
    return closest_fn


def search_kb(context_path):
    """
    Search the KB for the best-matching report by Ref No and Date/Time.
    Writes a result file to ../kb-search-result and returns a dict:
      { 'isMatchFound': bool, 'reportId': str }
    """
    # Parse ticket context
    ref_no, dt_str = parse_context(context_path)

    # Resolve paths
    ctx_dir = os.path.dirname(context_path)
    report_dir = os.path.abspath(os.path.join(ctx_dir, os.pardir, REPORT_FOLDER_NAME))
    result_dir = os.path.abspath(os.path.join(ctx_dir, os.pardir, RESULT_FOLDER_NAME))
    os.makedirs(result_dir, exist_ok=True)

    # Find match
    match_fn = find_best_match(ref_no, dt_str, report_dir)
    is_found = match_fn is not None

    # Write human-readable result
    base = os.path.splitext(os.path.basename(context_path))[0]
    out_path = os.path.join(result_dir, f"{base}_result.txt")
    with open(out_path, 'w', encoding='utf-8') as out:
        if is_found:
            out.write(f"Found matching report: {match_fn}\n")
        else:
            out.write("No matching report found.\n")

    return { 'isMatchFound': is_found, 'reportId': match_fn or '' }
