import os
import re
import spacy
from spacy.cli import download as spacy_download
from dataclasses import dataclass
from typing import Optional

# Load spaCy English model (ensure 'en_core_web_sm' is installed)
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

@dataclass
class Context:
    problem: Optional[str] = None
    date_time: Optional[str] = None
    reference_id: Optional[str] = None
    project: Optional[str] = None

    def __str__(self):
        parts = []
        if self.problem:
            parts.append(f"Problem: {self.problem}")
        if self.date_time:
            parts.append(f"Date/Time: {self.date_time}")
        if self.reference_id:
            parts.append(f"Ref No.: {self.reference_id}")
        if self.project:
            parts.append(f"Project: {self.project}")
        return "\n".join(parts)

class GatherContext:
    def __init__(self):
        pass

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

        # Second pass: spaCy NER fallback
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in ("DATE", "TIME") and not ctx.date_time:
                ctx.date_time = ent.text
            if ent.label_ == "CARDINAL" and not ctx.reference_id:
                ctx.reference_id = ent.text
        return ctx

# Top-level function to extract and write context

def gather_context(file_path: str) -> Context:
    """
    Reads a ticket text file, extracts context, writes it to ../contexts, and returns the Context.
    """
    # Read input ticket
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Extract
    gatherer = GatherContext()
    context = gatherer.gather(text)

    # Prepare output path
    input_dir = os.path.dirname(os.path.abspath(file_path))
    output_dir = os.path.abspath(os.path.join(input_dir, '..', 'contexts'))
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    out_file = f"{base_name}_context.txt"
    out_path = os.path.join(output_dir, out_file)

    # Write context
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(str(context))
    print(f"Context written to {out_path}")

    return context
