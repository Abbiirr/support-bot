#!/usr/bin/env python3
import os

class Ticket:
    def __init__(self, ticket_id: str, title: str, description: str, metadata: dict):
        self.ticket_id = ticket_id
        self.title = title
        self.description = description
        self.metadata = metadata


def read_ticket_from_text(raw_text: str) -> Ticket:
    """
    Parse a plain-text ticket from raw input. Assumes the first non-empty line is the title
    and the entire text is the description. Extracts ExtID as ticket_id if present in a line starting with 'ExtID:'.

    Returns:
        Ticket: with ticket_id (ExtID or empty), title, description, metadata containing extId if found.
    """
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    title = lines[0] if lines else ''
    description = raw_text.strip()

    # Extract ExtID if present
    ext_id = ''
    for line in lines:
        if line.lower().startswith('extid:'):
            ext_id = line.split(':', 1)[1].strip()
            break

    metadata = {}
    if ext_id:
        metadata['extId'] = ext_id

    return Ticket(ticket_id=ext_id, title=title, description=description, metadata=metadata)


def gather_context(ticket: Ticket) -> str:
    """
    Combine the ticket title and description into a single context string.

    Returns:
        str: context for search or logging.
    """
    return f"{ticket.title}\n{ticket.description}"


def generate_ack_reply(ticket: Ticket) -> str:
    """
    Generate a simple acknowledgment message for the given ticket.

    Returns:
        str: acknowledgment text.
    """
    if ticket.ticket_id:
        return f"Ticket {ticket.ticket_id}: Thank you for reporting this issue, we're investigating."
    return "Thank you for reporting this issue, we're investigating."


def read_and_reply(ticket_filename: str) -> None:
    """
    Read a plain-text ticket from the ../tickets folder, generate context and reply,
    and write them separately to ../context and ../replies folders.

    The context file is named:    ../context/<base>_context.txt
    The reply file is named:      ../replies/<base>_reply.txt
    where <base> is the ticket filename without extension.
    """
    # Determine directories
    base_dir = os.path.dirname(__file__)
    tickets_dir = os.path.join(base_dir, '..', 'tickets')
    context_dir = os.path.join(base_dir, '..', 'context')
    replies_dir = os.path.join(base_dir, '..', 'replies')

    # Create output directories if they don't exist
    os.makedirs(context_dir, exist_ok=True)
    os.makedirs(replies_dir, exist_ok=True)

    # Read the ticket text
    ticket_path = os.path.join(tickets_dir, ticket_filename)
    with open(ticket_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    # Process ticket
    ticket = read_ticket_from_text(raw_text)
    context = gather_context(ticket)
    reply = generate_ack_reply(ticket)

    # Derive base filename (without extension)
    base, _ = os.path.splitext(ticket_filename)
    context_path = os.path.join(context_dir, f"{base}_context.txt")
    reply_path = os.path.join(replies_dir, f"{base}_reply.txt")

    # Write context to ../context
    with open(context_path, 'w', encoding='utf-8') as ctx_file:
        ctx_file.write(context)

    # Write reply to ../replies
    with open(reply_path, 'w', encoding='utf-8') as rep_file:
        rep_file.write(reply)

    print(f"Context written to {context_path}")
    print(f"Reply written to {reply_path}")
