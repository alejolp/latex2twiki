#!/usr/bin/env python
# coding: utf-8

"""
LaTeX to twiki converter
------------------------

By Alejandro Santos, @alejolp.

This is a simple tokenizer based converter, to convert a latex text document
to twiki syntax (for my employer's internal wiki).
"""

import codecs
import os
import pprint
import string
import sys

SYMS = "{}[]"
OTHER_SYMS = "*"
QUOT = "`'´"
LETTERS = string.ascii_letters 

def tokenize_file(file_name):
    encoding = 'utf-8' # FIXME
    toks = []
    with codecs.open(file_name, 'r', encoding=encoding) as f:
        i = 0
        start = 0
        S = f.read()
        while i < len(S):
            if S[i] in SYMS or S[i] in OTHER_SYMS:
                if start < i:
                    toks.append(S[start:i])
                toks.append(S[i])
                i = i + 1
                start = i
            elif S[i] == '\\' and (i+1) < len(S) and S[i+1] in LETTERS:
                if start < i:
                    toks.append(S[start:i])
                start = i
                i = i + 1
                while i < len(S) and S[i] in LETTERS:
                    i = i + 1
                t = S[start:i]
                toks.append(t)
                start = i
            elif S[i] == '\n':
                if start < i:
                    toks.append(S[start:i])
                toks.append('\n')
                i = i + 1
                start = i
            elif S[i] in QUOT:
                if start < i:
                    toks.append(S[start:i])
                start = i
                while i < len(S) and S[i] in QUOT and S[i] == S[start]:
                    i = i + 1
                toks.append(S[start:i])
                start = i                
            else:
                i = i + 1
    return toks

def convert_to_twiki(toks):
    i = 0
    doc_begin = False
    stack = []
    cmd_item = False
    while i < len(toks):
        #print(toks[i])
        if doc_begin:
            if toks[i].startswith("\\") and toks[i][1] in LETTERS:
                if toks[i] == '\\begin':
                    assert toks[i+1] == '{'
                    if toks[i+2] == 'verbatim':
                        sys.stdout.write("<verbatim>")
                        i = i + 4
                    elif toks[i+2] in ('quote', 'quotation'):
                        sys.stdout.write("<bloquote>")
                        i = i + 4
                    elif toks[i+2] == 'description':
                        i = i + 4
                    elif toks[i+2] == 'enumerate':
                        i = i + 4
                    elif toks[i+2] == 'itemize':
                        i = i + 4
                    elif toks[i+2] == 'minipage':
                        i = i + 4
                    else:
                        i = i + 1
                elif toks[i] == '\\end':
                    assert toks[i+1] == '{'
                    if toks[i+2] == 'verbatim':
                        sys.stdout.write("</verbatim>")
                        i = i + 4
                    elif toks[i+2] in ('quote', 'quotation'):
                        sys.stdout.write("</bloquote>")
                        i = i + 4
                    elif toks[i+2] == 'document':
                        doc_begin = False
                        i = i + 4
                    elif toks[i+2] == 'description':
                        i = i + 4
                    elif toks[i+2] == 'enumerate':
                        i = i + 4
                    elif toks[i+2] == 'itemize':
                        i = i + 4
                    elif toks[i+2] == 'minipage':
                        i = i + 4
                    else:
                        i = i + 1
                elif toks[i] == '\\sec':
                    # Ignored
                    i = i + 4
                elif toks[i] == '\\label':
                    # Ignored
                    i = i + 4
                elif toks[i] == '\\ref':
                    # Ignored
                    i = i + 4
                elif toks[i] == '\\url':
                    assert toks[i+1] == '{' and toks[i+3] == '}'
                    sys.stdout.write("[[" + toks[i+2] + "][" + toks[i+2] + "]]")
                    i = i + 4
                elif toks[i] == '\\texttt':
                    i = i + 1
                    assert toks[i] == '{'
                    i = i + 1
                    stack.append(('{', '= '))
                    sys.stdout.write(" =")
                elif toks[i] == '\\textbf':
                    i = i + 1
                    assert toks[i] == '{'
                    i = i + 1
                    stack.append(('{', '* '))
                    sys.stdout.write(" *")
                elif toks[i] == '\\textit':
                    i = i + 1
                    assert toks[i] == '{'
                    i = i + 1
                    stack.append(('{', '_ '))
                    sys.stdout.write(" _")
                elif toks[i] == '\\textbackslash':
                    sys.stdout.write("\\")
                    i = i + 1
                elif toks[i] == '\\item':
                    sys.stdout.write("   * ")
                    cmd_item = True
                    i = i + 1

                    if toks[i] == '[':
                        i = i + 1
                        stack.append(('[', '*'))
                        sys.stdout.write("*")
                elif toks[i] == '\\section':
                    sys.stdout.write("---+ ")
                    i = i + 1
                    if toks[i] == '*':
                        i = i + 1
                elif toks[i] == '\\subsection':
                    sys.stdout.write("---++ ")
                    i = i + 1
                    if toks[i] == '*':
                        i = i + 1
                elif toks[i] == '\\subsubsection':
                    sys.stdout.write("---+++ ")
                    i = i + 1
                    if toks[i] == '*':
                        i = i + 1
                else:
                    i = i + 1
            elif toks[i] in SYMS:
                if toks[i] == '{':
                    stack.append((toks[i], None))
                elif toks[i] == '}':
                    symbol, closing = stack.pop(-1)
                    #print("\n\n$$$", repr(stack), repr(symbol), repr(closing))
                    assert symbol == '{'
                    if closing is not None:
                        sys.stdout.write(closing)
                elif '{' not in [a for a, b in stack]:
                    if toks[i] == '[':
                        stack.append((toks[i], None))
                    elif toks[i] == ']':
                        symbol, closing = stack.pop(-1)
                        assert symbol == '['
                        if closing is not None:
                            sys.stdout.write(closing)
                    else:
                        assert False
                i = i + 1
            elif toks[i] in QUOT:
                i = i + 1
            else:
                out = toks[i].replace("\\_", "_")
                if len(stack) > 0:
                    out = out.replace("<", "&lt;").replace(">", "&gt;")
                sys.stdout.write(out)
                i = i + 1
        elif toks[i] == '\n':
            cmd_item = False
            sys.stdout.write(toks[i])
            i = i + 1
        else:
            if toks[i] == '\\begin':
                assert toks[i+1] == '{'
                if toks[i+2] == 'document':
                    doc_begin = True
                    i = i + 4
                else:
                    i = i + 1
            else:
                i = i + 1

def main():
    file_name = sys.argv[1]

    toks = tokenize_file(file_name)
    #pprint.pprint(toks)

    convert_to_twiki(toks)

if __name__ == '__main__':
    main()
