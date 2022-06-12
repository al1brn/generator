#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 09:00:41 2022

@author: alain.bernard@loreal.com
"""

import re
import pprint

# ----------------------------------------------------------------------------------------------------
# Simple parser

class Parser:
    def __init__(self, text):
        self.text   = text
        self.cursor = 0
        
    @classmethod
    def FromFile(cls, fname):
        with open(fname) as f:
            return cls(f.read())
        
    def __str__(self):
        return self.text
    
    def __len__(self):
        return len(self.text)
    
    def __getitem__(self, index):
        return self.text[index]
        
    @property
    def eol(self):
        if self.eof:
            return True
        else:
            return self.text[self.cursor] == "\n"
        
    @property
    def eof(self):
        return self.cursor >= len(self.text)
    
    def back(self):
        self.cursor -= 1
        
    @property
    def read(self):
        if self.eof:
            return None
        self.cursor += 1
        return self.text[self.cursor-1]
    
    @property
    def current(self):
        if self.eof:
            return None
        else:
            return self.text[self.cursor]
    
    @property
    def previous(self):
        if self.cursor == 0:
            return None
        else:
            return self.text[self.cursor-1]
    
    def equal(self, s):
        if self.eof:
            return False
        return self.text[self.cursor:self.cursor + len(s)] == s
    
    
    # ---------------------------------------------------------------------------
    # Parse the content by lines
    # The source itself is scanned to pass the strings
    # The multi string are returned as a whole
    
    def python_split(self):
        
        self.cursor = 0
        context = 'SOURCE'
        txt     = ""
        while not self.eof:
            
            prev = self.previous
            c = self.read
            
            # ---------------------------------------------------------------------------
            # Source context : we can switch
            # - Comment #
            # - String '
            # - String "
            # - Comment multi lines """ ... """
            
            if context == 'SOURCE':
                
                if c == '#':
                    context = '#'
                    
                elif c == "'":
                    context = 'STRING'
                    quote   = c
                    raw_str = prev == 'r'
                    
                elif c == '"':
                    if self.equal('""'):
                        self.cursor += 2
                        context = 'COMMENT'
                        if txt != "":
                            # Return start of the line if different from spaces only
                            # otherwise keeps the spaces
                            if txt != " " * len(txt):
                                yield 'SOURCE', txt
                                txt = ""
                        c = None
                        
                    else:
                        context = 'STRING'
                        quote = c
                        raw_str = prev == 'r'
                        
                elif c == "\n":
                    yield 'SOURCE', txt
                    txt = ""
                    c = None
                    
            # ---------------------------------------------------------------------------
            # Comment multi lines: looking for """
                        
            elif context == 'COMMENT':
        
                if c == '"' and self.equal('""'):
                    self.cursor += 2
                    context = 'SOURCE'
                    yield 'COMMENT', txt
                    txt = ""
                    c = None
                
            # ---------------------------------------------------------------------------
            # String context:
            # - Passing the \?
            # - Looking for quote
                        
            elif context == 'STRING':
                
                if not raw_str and (c == '\\'):
                    c += self.read
                    
                elif c == quote:
                    context = 'SOURCE'
                    
            # ---------------------------------------------------------------------------
            # Comment #: looking for eol
                    
            elif context == '#':
                
                if c == "\n":
                    context = "SOURCE"
                    if txt != "":
                        yield 'SOURCE', txt
                        txt = ""
                    c = None

            # ---------------------------------------------------------------------------
            # Idiot proof
                    
            else:
                raise RuntimeError(f"Unknown context {context}")
                
            # ---------------------------------------------------------------------------
            # Let's consume the char
                    
            if c is not None:
                txt += c
        
        if txt != "":
            yield 'SOURCE', txt
            
    # ---------------------------------------------------------------------------
    # Return the source code in blocks of lines of the same type
    # - Source code
    # - Comment lines (starting by #)
    # - Comment (multi lines string)
    
    def to_packets(self):
        
        self.cursor = 0
        
        packets = []
        for context, raw_line in self.python_split():
            
            if raw_line.strip() == "":
                if packets:
                    packets[-1][2].append("")
                else:
                    packets = [('SOURCE', 0, [""])]
                continue
            
            
            # ----- Starting comment

            if context == 'SOURCE':

            # ----- Indentation and line from first non space char
            
                match  = re.search("(\s*)([^\s].*)", raw_line)
                indent = 0 if match.group(1) is None else len(match.group(1))
                line   = match.group(2)
                
                if line[0] == '#':
                    context = "COMMENT"
                    line = line[2:].strip()
                    if len(line) > 5 and line[0] in ['-', '=', '*']:
                        if line == line[0]*len(line):
                            line = ""

                lines = [line]
            
            # ----- Ensure the first line of a block comment is indented
                    
            elif context == 'COMMENT':
                
                lines = raw_line.split("\n")
                indent = 0
                
                if lines:
                    indent = None
                    for i, line in enumerate(lines):
                        if line.strip() == "":
                            continue
                        
                        match  = re.search("(\s*)([^\s].*)", line)
                        idt = 0 if match.group(1) is None else len(match.group(1))
                        if indent is None:
                            indent = idt
                        else:
                            indent = min(indent, idt)
                    if indent is None:
                        indent = 0
                
            # ----- Append the lines of new packet
            
            new = True
            if packets:
                if context == packets[-1][0] and indent == packets[-1][1]:
                    packets[-1][2].extend(lines)
                    new = False
            
            if new:
                packets.append((context, indent, lines))
                
        return packets
    
    # ---------------------------------------------------------------------------
    # Return classes and functions from a python file
    
    def documentation(self):
        
        # ---------------------------------------------------------------------------
        # Works on types indented packets
        
        packets = self.to_packets()
        
        # ---------------------------------------------------------------------------
        # Let's loop on these packets
        
        class Doc:
            def __init__(self, match):
                self.is_class = match.group(1) == 'class'
                self.name     = match.group(2)
                self.bef_comment  = ""
                self.aft_comment  = ""
                
                if self.is_class:
                    content_pat = r"\s*\((.*)\)"
                    m = re.search(content_pat, match.group(3))
                    if m is None:
                        self.bases = []
                    else:
                        self.bases = m.group(1).split(',')
                    self.funcs = {}
                    
                else:
                    self.class_doc  = None
                    self.args       = match.group(3)
                    self.decorators = []
                    
            @property
            def comment(self):
                return self.bef_comment if self.aft_comment == "" else self.aft_comment
            
            def __repr__(self):
                indent = "" if (self.is_class or self.class_doc is None) else "    "
                scomm = f"\n{indent}    | ".join([""] + self.comment.split("\n"))
                if self.is_class:
                    sfuncs = "\n".join([repr(func) for func in self.funcs.values()])
                    return f"{'='*100}\nclass {self.name}\n{scomm}\n{sfuncs}"
                else:
                    if self.decorators:
                        decs = f"\n{indent}".join([""] + self.decorators) + "\n"
                    else:
                        decs = ""
                    return f"{indent}{'-'*80}\n{decs}{indent}def {self.name}{self.args}\n{scomm}\n"
        
        docs = {}
        
        func_indent = 0
        read_index  = 0
        cur_class   = None
        
        while read_index < len(packets):
            
            packet = packets[read_index]
            packet_index = read_index
            read_index += 1
            
            # ----- Only source packets

            if packet[0] != 'SOURCE':
                continue
            
            # ----- Indentation is greater than the current function
            # we are within it
            
            indent = packet[1]
            if indent > func_indent:
                continue
            
            # ----- Normally, class of def header
            
            lines = packet[2]

            for line_index, line in enumerate(lines):
                
                match = re.search(r"(def|class)\s+(\w+)([^:]*)", line)
                if match is None:
                    continue
                
                # ----- Something found
                    
                doc = Doc(match)
                
                # ----- Let's ignore inner classes
                
                if doc.is_class and indent != 0:
                    break
                
                # ----- Do we have a comment before ?
                
                if packet_index > 0:
                    bef = packets[packet_index-1]
                    if bef[0] == 'COMMENT' and bef[1] == indent:
                        doc.bef_comment = "\n".join(bef[2])
                        
                # ----- Do we have a comment after ?

                aft = packets[packet_index+1]
                if packets[packet_index+1][0] == 'COMMENT':
                    if aft[0] == 'COMMENT':
                        doc.aft_comment = "\n".join(aft[2])
                        
                # ----- A new class
                
                if doc.is_class:
                    docs[doc.name] = doc
                    
                    cur_class   = doc
                    func_indent = 99
                    
                else:
                    for i in reversed(range(line_index)):
                        if lines[i] != "" and lines[i][0] == '@':
                            doc.decorators.append(lines[i])
                    
                    # Global function
                    if indent == 0:
                        docs[doc.name] = doc
                        cur_class   = None
                        func_indent = 0
                        
                    # Class method
                    else:
                        doc.class_doc = cur_class
                        cur_class.funcs[doc.name] = doc
                        func_indent = indent
                        
                break
            
        return docs
    
    




    
    
