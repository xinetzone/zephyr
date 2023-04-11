#!/usr/bin/env python3
# Copyright (c) 2022 Intel corporation
# SPDX-License-Identifier: Apache-2.0
import sys
import re

# Scratch register allocator.  Zephyr uses multiple Xtensa SRs as
# scratch space for various special purposes.  Unfortunately the
# configurable architecture means that not all registers will be the
# same on every device.  This script parses a pre-cooked ("gcc -E
# -dM") core-isa.h file for the current architecture and assigns
# registers to usages.

NEEDED = ("ALLOCA", "CPU", "FLUSH")

coreisa = sys.argv[1]
outfile = sys.argv[2]

syms = {}

def get(s):
    return syms[s] if s in syms else 0

with open(coreisa) as infile:
    for line in infile:
        if m := re.match(r"^#define\s+([^ ]+)\s*(.*)", line.rstrip()):
            syms[m[1]] = m[2]

# Use MISC registers first if available, that's what they're for
regs = [f"MISC{n}" for n in range(int(get("XCHAL_NUM_MISC_REGS")))]

# Next come EXCSAVE. Also record our highest non-debug interrupt level.
maxint = 0
for il in range(1, 1 + int(get("XCHAL_NUM_INTLEVELS"))):
    regs.append(f"EXCSAVE{il}")
    if il != int(get("XCHAL_DEBUGLEVEL")):
        maxint = max(il, maxint)

# Find the highest priority software interrupt.  We'll use that for
# arch_irq_offload().
irqoff_level = -1
irqoff_int = -1
for sym, val in syms.items():
    if val == "XTHAL_INTTYPE_SOFTWARE":
        if m := re.match(r"XCHAL_INT(\d+)_TYPE", sym):
            intnum = int(m[1])
            levelsym = f"XCHAL_INT{intnum}_LEVEL"
            if levelsym in syms:
                intlevel = int(syms[levelsym])
                if intlevel > irqoff_level:
                    irqoff_int = intnum
                    irqoff_level = intlevel

# Now emit our output header with the assignments we chose
with open(outfile, "w") as f:
    f.write("/* Generated File, see gen_zsr.py */\n")
    f.write("#ifndef ZEPHYR_ZSR_H\n")
    f.write("#define ZEPHYR_ZSR_H\n")
    for i, need in enumerate(NEEDED):
        f.write(f"# define ZSR_{need} {regs[i]}\n")
        f.write(f"# define ZSR_{need}_STR \"{regs[i]}\"\n")

    # Emit any remaining registers as generics
    for i in range(len(NEEDED), len(regs)):
        f.write(f"# define ZSR_EXTRA{i - len(NEEDED)} {regs[i]}\n")

    # Also, our highest level EPC/EPS registers
    f.write(f"# define ZSR_RFI_LEVEL {maxint}\n")
    f.write(f"# define ZSR_EPC EPC{maxint}\n")
    f.write(f"# define ZSR_EPS EPS{maxint}\n")

    # And the irq offset interrupt
    if irqoff_int >= 0:
        f.write(f"# define ZSR_IRQ_OFFLOAD_INT {irqoff_int}\n")

    f.write("#endif\n")
