#!/usr/bin/env python3
#
# Copyright (c) 2022, Nordic Semiconductor ASA
#
# SPDX-License-Identifier: Apache-2.0

'''
Script to generate image information files.

This script creates a image information header which can be included by a
second build system.
This allows a second stage build system to use image information from a Zephyr
build by including the generated header.

Information included in the image information header:
- Number of segments in the image
- LMA address of each segment
- VMA address of each segment
- LMA adjusted of each segment if the LMA addresses has been adjusted after linking
- Size of each segment
'''

import argparse
import re
from elftools.elf.elffile import ELFFile


def write_header(filename, segments, adjusted_lma):
    filename_we = re.sub(r'[\W]','_', filename).upper()
    content = [
        f'#ifndef {filename_we}_H',
        f'#define {filename_we}_H',
        f'',
        f'#define SEGMENT_NUM {len(segments)}',
        f'#define ADJUSTED_LMA {adjusted_lma}',
    ]
    for idx, segment in enumerate(segments):
        segment_header = segment['segment'].header
        hex_lma_addr = hex(segment_header.p_paddr)
        hex_vma_addr = hex(segment_header.p_vaddr)
        hex_size = hex(segment_header.p_filesz)

        content.extend(
            (
                f'',
                f'#define SEGMENT_LMA_ADDRESS_{idx} {hex_lma_addr}',
                f'#define SEGMENT_VMA_ADDRESS_{idx} {hex_vma_addr}',
                f'#define SEGMENT_SIZE_{idx} {hex_size}',
            )
        )
    content.extend((f'', f'#endif /* {filename_we}_H */'))
    with open(filename, 'w') as out_file:
        out_file.write('\n'.join(content))


def read_segments(filename):
    elffile = ELFFile(open(filename, 'rb'))
    segments = []
    for segment_idx in range(elffile.num_segments()):
        segments.insert(segment_idx, {})
        segments[segment_idx]['segment'] = elffile.get_segment(segment_idx)
    return segments


def main():
    parser = argparse.ArgumentParser(description='''
    Process ELF file and extract image information.
    Create header file with extracted image information which can be included
    in other build systems.''', allow_abbrev=False)

    parser.add_argument('--header-file', required=True,
                        help="""Header file to write with image data.""")
    parser.add_argument('--elf-file', required=True,
                        help="""ELF File to process.""")
    parser.add_argument('--adjusted-lma', required=False, default=0,
                        help="""Adjusted LMA address value.""")
    args = parser.parse_args()

    segments = read_segments(args.elf_file)
    write_header(args.header_file, segments, args.adjusted_lma)


if __name__ == "__main__":
    main()
