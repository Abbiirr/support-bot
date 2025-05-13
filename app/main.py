#!/usr/bin/env python3
from ticket_reader import read_and_reply


def main():
    # Hardcoded ticket filename; change as needed
    ticket_filename = "ticket_0001.txt"
    read_and_reply(ticket_filename)


if __name__ == '__main__':
    main()
