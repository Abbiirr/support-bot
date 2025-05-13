#!/usr/bin/env python3
from ticket_reader import read_and_reply
from gather_context import gather_context



def main():
    # Hardcoded ticket filename; change as needed
    ticket_filename = "ticket_0001.txt"
    read_and_reply(ticket_filename)
    gather_context("../tickets/ticket_0001.txt")


if __name__ == '__main__':
    main()
