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
    project: Optional[str] = None
    problem: Optional[str] = None
    date_time: Optional[str] = None
    reference_id: Optional[str] = None
    user_id: Optional[str] = None
    account_no: Optional[str] = None
    error_code: Optional[str] = None

    def __str__(self):
        parts = []
        if self.ticket:
            parts.append(f"Ticket: {self.ticket}")
        if self.project:
            parts.append(f"Project: {self.project}")
        if self.problem:
            parts.append(f"Problem: {self.problem}")
        if self.date_time:
            parts.append(f"Date/Time: {self.date_time}")
        if self.reference_id:
            parts.append(f"Ref No.: {self.reference_id}")
        if self.user_id:
            parts.append(f"UserID: {self.user_id}")
        if self.account_no:
            parts.append(f"Account No: {self.account_no}")
        if self.error_code:
            parts.append(f"Error Code: {self.error_code}")
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
            if not ctx.reference_id:
                m = REF_ID_PATTERN.search(line)
                if m:
                    ctx.reference_id = m.group(1).strip()
            if not ctx.project:
                m = PROJECT_PATTERN.search(line)
                if m:
                    ctx.project = m.group(1).strip()
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

        # Use default project if missing
        if not ctx.project and self.default_project:
            ctx.project = self.default_project

        # Second pass: spaCy NER fallback for date/time and IDs
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in ("DATE", "TIME") and not ctx.date_time:
                ctx.date_time = ent.text
            if ent.label_ == "CARDINAL" and not ctx.reference_id:
                # fallback to any cardinal as reference if missing
                ctx.reference_id = ent.text
        return ctx

# Top-level function to extract and write context
# Accepts ticket filename and optional default_project
def gather_context(ticket_name: str, default_project: Optional[str] = None) -> Context:
    """
    Reads a ticket text file from ../tickets by ticket_name, extracts context,
    writes it to ../contexts, and returns the Context.
    """
    base_dir = os.path.dirname(__file__)
    tickets_dir = os.path.abspath(os.path.join(base_dir, '..', 'tickets'))
    file_path = os.path.join(tickets_dir, ticket_name)

    # Read input ticket
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Extract with optional default project
    gatherer = GatherContext(default_project=default_project)
    context = gatherer.gather(text)

    # Set ticket number from filename
    context.ticket = os.path.splitext(ticket_name)[0]

    # Prepare output path
    contexts_dir = os.path.abspath(os.path.join(tickets_dir, '..', 'contexts'))
    os.makedirs(contexts_dir, exist_ok=True)
    out_file = f"{context.ticket}_context.txt"
    out_path = os.path.join(contexts_dir, out_file)

    # Write context
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(str(context))

    return context