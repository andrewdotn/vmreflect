#!/usr/bin/python2.7
# coding: UTF-8

"""
Zero out the TimeDateStamp header in a PE file, to make builds reproducible.

The pefile module automatically updates the PE file’s checksum header.
"""

import argparse
import pefile

def zero(filename):
    """Zero out the TimeDateStamp PE header in filename, and save to disk."""
    pe = pefile.PE(filename)
    pe.FILE_HEADER.TimeDateStamp = 0
    pe.OPTIONAL_HEADER.CheckSum = pe.generate_checksum()
    if not pe.verify_checksum():
        raise Exception("verify_checksum() failed")
    pe.write(filename=filename)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('PEFILE', help="""The PE file to zero out the
                        TimeDateStamp header in.""")
    args = parser.parse_args()
    zero(args.PEFILE)
