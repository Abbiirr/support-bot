import os
import re
import spacy
from spacy.cli import download as spacy_download
from dataclasses import dataclass
from typing import Optional

# Load spaCy English model, auto-download if missing
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    spacy_download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Regex patterns for structured fields
DATE_TIME_PATTERN = re.compile(r"Date/Time[:]?\s*(.*)")
REF_ID_PATTERN = re.compile(r"(?:ExtID|Ref\.?\s*No\.?|Reference ID)[:]?\s*([A-Za-z0-9_-]+)")
PROJECT_PATTERN = re.compile(r"Project[:]?\s*(.*)")
PROBLEM_PATTERN = re.compile(r"(?i)(?:observed the following|problem)\s*(.*)")
USER_ID_PATTERN = re.compile(r"UserID[:]?\s*(.+)")
ACCOUNT_PATTERN = re.compile(r"Account\s*No[:]?\s*(.+)")
ERROR_CODE_PATTERN = re.compile(r"Error\s*Code[:]?\s*(.+)")

@dataclass
class Context:
    ticket: Optional[str] = None
    problem: Optional[str] = None
    date_time: Optional[str] = None
    reference_id: Optional[str] = None
    project: Optional[str] = None
    user_id: Optional[str] = None
    account_no: Optional[str] = None
    error_code: Optional[str] = None

    def __str__(self):
        parts = []
        if self.ticket:
            parts.append(f"Ticket: {self.ticket}")
        if self.problem:
            parts.append(f"Problem: {self.problem}")
        if self.date_time:
            parts.append(f"Date/Time: {self.date_time}")
        if self.user_id:
            parts.append(f"UserID: {self.user_id}")
        if self.account_no:
            parts.append(f"Account No: {self.account_no}")
        if self.error_code:
            parts.append(f"Error Code: {self.error_code}")
        if self.reference_id:
            parts.append(f"Ref No.: {self.reference_id}")
        if self.project:
            parts.append(f"Project: {self.project}")
        return "\n".join(parts)

class GatherContext:
    def __init__(self, default_project: Optional[str] = None):
        """
        :param default_project: a fallback project name if not found in text
        """
        self.default_project = default_project

    def gather(self, text: str) -> Context:
        ctx = Context()

        # First pass: regex extraction per line
        for line in text.splitlines():
            if not ctx.problem:
                m = PROBLEM_PATTERN.search(line)
                if m:
                    ctx.problem = m.group(1).strip().capitalize()
            if not ctx.date_time:
                m = DATE_TIME_PATTERN.search(line)
                if m:
                    ctx.date_time = m.group(1).strip()
            if not ctx.user_id:
                m = USER_ID_PATTERN.search(line)
                if m:
                    ctx.user_id = m.group(1).strip()
            if not ctx.account_no:
                m = ACCOUNT_PATTERN.search(line)
                if m:
                    ctx.account_no = m.group(1).strip()
            if not ctx.error_code:
                m = ERROR_CODE_PATTERN.search(line)
                if m:
                    ctx.error_code = m.group(1).strip()
            if not ctx.reference_id:
                m = REF_ID_PATTERN.search(line)
                if m:
                    ctx.reference_id = m.group(1).strip()
            if not ctx.project:
                m = PROJECT_PATTERN.search(line)
                if m:
                    ctx.project = m.group(1).strip()

        # If project still missing, use default
        if not ctx.project and self.default_project:
            ctx.project = self.default_project

        # Second pass: spaCy NER fallback for date/time and IDs
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in ("DATE", "TIME") and not ctx.date_time:
                ctx.date_time = ent.text
            if ent.label_ == "CARDINAL" and not ctx.user_id:
                ctx.user_id = ent.text
        return ctx

# Top-level function to extract and write context
# Accepts optional default_project parameter

def gather_context(ticket_name: str, default_project: Optional[str] = None) -> Context:
    base_dir = os.path.dirname(__file__)
    tickets_dir = os.path.join(base_dir, '..', 'tickets')
    file_path = os.path.join(tickets_dir, ticket_name)
    """
    Reads a ticket text file, extracts context (using default_project if needed),
    writes it to ../contexts, and returns the Context.
    """
    # Read input ticket
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Extract with optional default project
    gatherer = GatherContext(default_project=default_project)
    context = gatherer.gather(text)

    # Determine ticket number from filename
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    context.ticket = base_name

    # Prepare output path
    input_dir = os.path.dirname(os.path.abspath(file_path))
    output_dir = os.path.abspath(os.path.join(input_dir, '..', 'contexts'))
    os.makedirs(output_dir, exist_ok=True)

    out_file = f"{base_name}_context.txt"
    out_path = os.path.join(output_dir, out_file)

    # Write context
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(str(context))

    print(f"Context written to {out_path}")

    return context
