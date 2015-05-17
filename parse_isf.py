# -*- coding: utf-8 -*-
"""
Created on Fri May 15 17:26:45 2015

@author: Sebastian Theilenberg
"""

import numpy as np
import os.path


def parse_curve(isf_file):
    """
    Reads one tektronix .isf file and returns a dictionary containing
    all tags as keys. The actual data is stored in the key "data".
    """
    extensions = set([".isf"])
    if os.path.splitext(isf_file)[-1].lower() not in extensions:
        raise ValueError("File type unkown.")

    with open(isf_file, 'rb') as ifile:
        # read header
        header = {}
        currentposition = 0
        while True:
            currentposition, name = _read_chunk(ifile, " ")
            if name != ":CURVE":
                currentposition, value = _read_chunk(ifile, ";")

                assert name not in header
                header[name] = value
            else:
                # ":CURVE " is the last tag of the header, followed by
                # '#XYYY' with X being the number of bytes of YYY.
                # YYY is the length of the datastream following in bytes.
                value = ifile.read(2)
                y_str = ifile.read(int(value[-1]))
                value += y_str

                assert int(y_str) == (
                    int(header["NR_PT"]) * int(header[":WFMPRE:BYT_NR"])
                    )
                header[name] = value
                currentposition = ifile.tell()
                break

        assert header["ENCDG"] == "BINARY"

        # read data as numpy array
        header["data"] = _read_data(ifile, currentposition, header)

    return header


def _read_chunk(headerfile, delimiter):
    """
    Reads one chunk of header data. Based on delimiter, this may be a tag
    (ended by " ") or the value of a tag (ended by ";").
    """
    prior_delimiter = None
    chunk = []
    while True:
        c = headerfile.read(1)
        if c != delimiter:
            chunk.append(c)
            if c == '"':
                # switch delimiter to make sure to parse the whole string
                # enclosed in '"'.
                delimiter, prior_delimiter = c, delimiter
        elif prior_delimiter:
            # switch back delimiter
            chunk.append(c)
            delimiter, prior_delimiter = prior_delimiter, None
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
