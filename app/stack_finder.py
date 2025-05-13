#!/usr/bin/env python3
import os
from typing import Dict, List, Optional

# Issue categories with associated keywords
ISSUE_KEYWORDS: Dict[str, List[str]] = {
    'backend': ['database', 'db', 'api', 'server', 'integration', 'transaction', 'error', 'exception', 'timeout',
                'kafka'],
    'frontend': ['ui', 'button', 'css', 'javascript', 'layout', 'responsive', 'screen', 'html', 'react', 'angular',
                 'vue'],
    'app': ['mobile', 'android', 'ios', 'app', 'crash', 'install', 'update', 'version', 'apk'],
    'network': ['network', 'timeout', 'connection', 'latency', 'dns', 'http', 'tcp', 'udp', 'ssl', 'tls', 'slow',
                'delay', 'delays', 'load', 'performance']
}

# Output folder for stack classification\;
STACK_FOUND_FOLDER = 'stack-found'


def find_stack(context_path: Optional[str], ticket_path: str) -> str:
    """
    Classify an issue as backend, frontend, app, or network based on keyword matching
    in the context text. Handles missing or null context_path gracefully.
    Writes the classification to ../stack-found/{ticket_name}_classification.txt,
    prints the classification, and returns it.

    Args:
      context_path: Optional path to the context file containing ticket details.
      ticket_path: Path to the original ticket file (for naming output).

    Returns:
      The identified issue category.
    """
    # Safely read context content
    text = ''
    if context_path and os.path.isfile(context_path):
        with open(context_path, 'r', encoding='utf-8') as f:
            text = f.read().lower()

    # Score each category by counting keyword occurrences
    scores = {category: 0 for category in ISSUE_KEYWORDS}
    for category, keywords in ISSUE_KEYWORDS.items():
        for kw in keywords:
            scores[category] += text.count(kw)

    # If text is empty or no keywords matched, default to 'network' for service slowness contexts
    if not text or all(score == 0 for score in scores.values()):
        best_category = 'network'
    else:
        # Determine best category by highest score
        best_category, best_score = 'unknown', 0
        for category, score in scores.items():
            if score > best_score:
                best_category, best_score = category, score
        # If tie or zero, default to unknown

    # Determine base directory for output
    if context_path and os.path.isdir(os.path.dirname(context_path)):
        base_dir = os.path.dirname(context_path)
    else:
        base_dir = os.path.dirname(ticket_path)
    output_dir = os.path.abspath(os.path.join(base_dir, os.pardir, STACK_FOUND_FOLDER))
    os.makedirs(output_dir, exist_ok=True)

    # Determine ticket name and output path
    ticket_name = os.path.splitext(os.path.basename(ticket_path))[0]
    out_file = os.path.join(output_dir, f"{ticket_name}_classification.txt")

    # Write classification result
    with open(out_file, 'w', encoding='utf-8') as out:
        out.write(f"issue_type: {best_category}\n")

    # Print and return the classification
    print(f"Issue classified as: {best_category}")
    return best_category


# Example usage
if __name__ == '__main__':
    import sys

    ticket = sys.argv[1] if len(sys.argv) > 1 else None
    context = sys.argv[2] if len(sys.argv) > 2 else None
    find_stack(context, ticket)