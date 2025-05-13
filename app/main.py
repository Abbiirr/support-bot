#!/usr/bin/env python3
import os

from app.gather_context import gather_context
from ticket_reader import read_and_reply
from kb_searcher import search_kb
from bot_resolver import resolve_ticket
from stack_finder import find_stack


def main():
    # Hardcoded ticket filename (change as needed)
    base_dir = os.path.dirname(__file__)
    tickets_dir = os.path.join(base_dir, '..', 'tickets')

    ticket_filename = "ticket_0007.txt"
    ticket_path = os.path.join(base_dir, ticket_filename)
    # 1. Generate context and reply files
    read_and_reply(ticket_filename)
    gather_context(ticket_filename, "MMBL")
    # 2. Build absolute path to the generated context file
    base_dir = os.path.dirname(__file__)
    base = os.path.splitext(ticket_filename)[0]
    context_path = os.path.normpath(os.path.join(base_dir, '..', 'contexts', f"{base}_context.txt"))
    # find_stack(context_path, ticket_path)
    # 3. Search the knowledge base using correct path
    result = search_kb(context_path)
    if result.get('isMatchFound'):
        report_id = result.get('reportId', '')
        print(f"Match found in KB with report ID: {report_id}")
        # Proceed to resolution workflow
        resolve_ticket(context_path,report_id)
    else:
        print("No match found in KB, delegating to stack finder...")
        find_stack(context_path, ticket_path)

if __name__ == '__main__':
    main()
