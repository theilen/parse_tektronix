# -*- coding: utf-8 -*-
"""
Created on Fri May 15 17:26:45 2015

@author: Sebastian Theilenberg
"""

import numpy as np
import os.path


def parse_curve(binaryfile):
    """
    Reads one tektronix .isf file and returns a dictionary containing
    all tags as keys. The actual data is stored in the key "data".
    """
    extensions = set([".isf"])
    if os.path.splitext(binaryfile)[-1].lower() not in extensions:
        raise ValueError("File type unkown.")

    with open(binaryfile, 'rb') as bfile:

        # read header
        header = {}
        current = 0

        while True:

            current, name = _read_chunk(bfile, " ")

            if name != ":CURVE":
                current, value = _read_chunk(bfile, ";")

                assert name not in header
                header[name] = value
            else:
                # ":CURVE" is the last tag of the header, followed by
                # a '#' and a 7 digit number.
                header[name] = bfile.read(8)
                current = bfile.tell()
                break

        assert header["ENCDG"] == "BINARY"

        # read data as numpy array
        header["data"] = _read_data(bfile, current, header)

    return header


def _read_chunk(headerfile, delimiter):
    """
    Reads one chunk of header data. Based on delimiter, this may be a tag
    (ended by " ") or the value of a tag (ended by ";").
    """
    chunk = []
    while True:
        c = headerfile.read(1)
        if c != delimiter:
            chunk.append(c)
        else:
            return headerfile.tell(), "".join(chunk)


def _read_data(bfile, position, header):
    """
    Reads in the binary data as numpy array.
    Apparently, there are only 1d-signals stored in .isf files, so a 1d-array
    is read.
    """
    # determine the datatype from header tags
    datatype = ">" if header["BYT_OR"] == "MSB" else "<"
    if header["BN_FMT"] == "RI":
        datatype += "i"
    else:
        datatype += "u"
    datatype += header[":WFMPRE:BYT_NR"]

    bfile.seek(position)
    data = np.fromfile(bfile, datatype)
    assert data.size == int(header["NR_PT"])

    # calculate true values
    data = data * float(header["YMULT"]) + float(header["YZERO"])

    return data
