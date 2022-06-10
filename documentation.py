#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  3 16:40:15 2022

@author: alain.bernard@loreal.com
"""

import re

# ----------------------------------------------------------------------------------------------------
# Block: a list of blocks
#
# Inheritance:
# Text    : list of lines with a same depth
# Section : Non null title
# Doc     : A full document, top parent

class Block(list):
    
    def __init__(self, parent=None):
        self.parent = parent
        if parent is not None:
            parent.append(self)
        
    def __str__(self):
        s = ""
        for line in self.gen_text():
            s += line + "\n"
        return s
    
    def __repr__(self):
        
        s = f"{'    '*self.depth}<{type(self).__name__}, blocks={len(self)}>\n"
        for block in self:
            s += repr(block)
        return s
    
    # ------------------------------------------------------------------------------------------
    # The depth of the block

    @property
    def depth(self):
        if self.parent is None:
            return 0
        else:
            return 1 + self.parent.depth
        
    # ------------------------------------------------------------------------------------------
    # Access to the top block
        
    @property
    def top(self):
        if self.parent is None:
            return self
        else:
            return self.parent.top
        
    @property
    def doc(self):
        doc = self.top
        return doc if isinstance(doc, Doc) else None

    # ------------------------------------------------------------------------------------------
    # Text indentation for text output    
        
    @property
    def text_indent(self):
        doc = self.doc
        return ("    " if doc is None else doc.base_indent) * self.depth

    # ------------------------------------------------------------------------------------------
    # Text output
        
    def gen_text(self):
        for block in self:
            for line in block.gen_text():
                yield line
                
    # ------------------------------------------------------------------------------------------
    # Markdown output
        
    def gen_md(self):
        for block in self:
            for line in block.gen_md():
                yield line
                
                
# ----------------------------------------------------------------------------------------------------
# Text: a list of lines
#
# The prefix is used for lists (- or 1.) and evidence (>)          
        
class Text(Block):
    
    def __init__(self, parent=None, prefix=None):
        super().__init__(parent)
        self.prefix = "" if prefix is None else prefix
        self.lines  = []
        
    def __repr__(self):
        lines = [line[:10] for line in self.lines]
        s = f"{'    '*self.depth}<Text, blocks: {len(self)}, lines: {len(self.lines)}, prefix='{self.prefix}'> {lines}\n"
        for block in self:
            s += repr(block)
        return s
        
    # ------------------------------------------------------------------------------------------
    # Add lines
    
    def add_lines(self, *lines):
        for line in lines:
            self.lines.append(line)
            
    # ------------------------------------------------------------------------------------------
    # solve a link
    
    def solve_link(self, link):
        doc = self.doc
        return link if doc is None else doc.solve_link(link)

    # ------------------------------------------------------------------------------------------
    # Text output
    
    def gen_text(self):
        indent = self.text_indent
        first  = True
        for line in self.lines:
            if first:
                yield f"{indent}{self.prefix}{line}"
                indent += " " * len(self.prefix)
                first = False
            else:
                yield f"{indent}{line}"
                
        for line in super().gen_text():
            yield line
            
    # ------------------------------------------------------------------------------------------
    # Markdown output
        
    def gen_md(self):
        
        # ---------------------------------------------------------------------------
        # Replace a link by a solved link
        
        def solve(match):
            start = match.group(1)
            if start[0] == '!':
                return start + self.solve_link("image:" + match.group(2))
            else:
                return start + self.solve_link(match.group(2))
            
        def solve_src(match):
            return match.group(1) + self.solve_link("image:" + match.group(2))
        
        indent = ""

        # ------------------------------------------------------------
        # Loop on the lines
        
        first  = True
        for line in self.lines:
            
            # ----- Solve the image links

            # Markdown syntax
            
            line = re.sub(r"(!?\[[^\]]+\]\()([^)]+)", solve, line)
            
            # Html syntax

            line = re.sub(r'(<img\s+.*src\s*=\s*")([^"]+)', solve_src, line)
            
            # ----- Output
            
            if first:
                yield f"{indent}{self.prefix}{line}"
                first = False
                indent = " " * len(self.prefix)
            else:
                yield f"{indent}{line}"
                
        for line in super().gen_md():
            yield line
            
                
# ----------------------------------------------------------------------------------------------------
# Section: an entitled Block
                    
class Section(Block):
    
    md_title_pat  = re.compile(r"\s*(#+)\s(.*\n)")
    txt_title_pat = re.compile(r"\s*(.+\n)\s*([-=]+\n)")
    
    def __init__(self, parent=None, title=None, tag=None):
        super().__init__(parent)
        self.title = title
        self.tag_  = tag
        
    # ------------------------------------------------------------------------------------------
    # Tag property  

    @staticmethod
    def build_tag(title):
        return None if title is None else title.lower().replace(' ', '-').replace('.', '_')
    
    @property
    def tag(self):
        return Section.build_tag(self.title) if self.tag_ is None else self.tag_
    
    @tag.setter
    def tag(self, value):
        self.tag_ = value
        
    # ------------------------------------------------------------------------------------------
    # Access to the top section through path syntax:
    #
    # Classes reference.class Node.__init__ : section "__init__" in section "class Node" in "Classes reference"
        
    def get_section(self, path, use_tag = False):
        
        tags = path.split('.', 1)
        found = None
        for block in self:
            
            if not isinstance(block, Section):
                continue
            
            if block.tag is None:
                continue
            
            if use_tag:
                if block.tag == tags[0]:
                    found = block
            else:
                if block.title == tags[0]:
                    found = block
                    
            if found is not None:
                if len(tags) == 1:
                    return found
                else:
                    return found.get_section(tags[1])
                
        return None
    
    # ------------------------------------------------------------------------------------------
    # Implementation file
    
    
    
    @property
    def writing_folder(self):
        if hasattr(self, 'folder'):
            return self.folder
    
    @property
    def get_link(self):
        pass
        
    
    
    # ------------------------------------------------------------------------------------------
    # Tree of sections (for debug)
    
    def tree(self, mode=None):
        s = "    " * self.depth + str(self.title) + "\n"
        for block in self:
            if isinstance(block, Section):
                s += block.tree(mode=mode)
        return s
    
    # ------------------------------------------------------------------------------------------
    # Initialization from text
    
    def set_text(self, text):
        
        # ---------------------------------------------------------------------------
        # Split in sections
        
        txt_title_pat = re.compile(r"\s*(.+)\n\s*([-=]+)\n")
        md_title_pat  = re.compile(r"\s*(#+)\s(.*)")
        
        # Text format
        # -----------
        
        cursor   = 0
        levels   = []
        titles   = []
        texts    = []
        
        for match in txt_title_pat.finditer(text):
            
            titles.append(match.group(1))
            levels.append(1 if match.group(2)[0] == "=" else 2)
            texts.append(text[cursor:match.start()])
            cursor = match.end()
            
        if cursor > 0:
            texts.append(text[cursor:])
            
        # # md format
            
        else:
    
            for match in md_title_pat.finditer(text):
                
                titles.append(match.group(2))
                levels.append(len(match.group(1)))
                texts.append(text[cursor:match.start()])
                cursor = match.end()+1
    
            texts.append(text[cursor:])
            
        # ---------------------------------------------------------------------------
        # Normalize the sections levels
        
        if levels:
            min_level = min(levels)
            for i in range(len(levels)):
                levels[i] -= min_level
            
        # ---------------------------------------------------------------------------
        # Integrate the introductory text
        
        class Stacker:
            def __init__(self, block, indent, line_type=None, order=1):
                self.block     = block
                self.indent    = indent
                self.line_type = line_type
                self.order     = order
                
        stack = [Stacker(self, -1)]
        
        # ----- Loop on the lines
        
        for raw_line in texts[0].split("\n"):
    
            pattern = r"(^\s*)((([->]\s)|(\d+\.\s))?(.*))"
            match = re.search(pattern, raw_line)
            if match is None:
                raise RuntimeError("Very strange")
                
            indent = len(match.group(1))
            prefix = match.group(3)
            line   = match.group(6)
            
            # ----- Empty line
            
            if line.strip() == "":
                if len(stack) > 1: # First line
                    stack[-1].block.add_lines("")
                continue
            
            # ----- Line type
            
            if prefix is None:
                line_type = 'TEXT'
                
            else:
                indent += len(prefix)
                
                if prefix == '- ':
                    line_type = 'LIST'
                    
                elif prefix == '> ':
                    line_type = 'EVIDENCE'
                    
                elif len(re.findall("\d+\.", prefix)) == 1:
                    line_type = "ORDERED"
                    
                else:
                    raise RuntimeError(f"Unknown line type '{prefix}' in line: {raw_line}")
                    
            # ---------------------------------------------------------------------------
            # Compare the current indentation with the current one
            #
            # If equal
            #     basically we add the line to the current block (top of the stack)
            #     but before we check if it is a new list item. In that case, we have
            #     to crate a new block and to replace to top of the stack with it
            #
            # If different
            #     we create necessarily a new block
            #         either at the top of the stack if deeper indentation
            #         if shallower, we must first pop the stack
                    
            if indent == stack[-1].indent:
                
                # ----- TEXT: always happened to the current block
                
                if line_type == 'TEXT':
                    stack[-1].block.add_lines(line)
                    
                # ----- OTHER but equal: we create an new block for lists
                    
                elif line_type == stack[-1].line_type:
                    
                    if line_type == 'EVIDENCE':
                        stack[-1].block.add_lines(line)
                    
                    else:
                        if line_type == 'ORDERED':
                            stack[-1].order += 1
                            prefix = f"{stack[-1].order}. "
                            
                        block = Text(parent=stack[-2].block, prefix=prefix)
                        block.add_lines(line)
                        stack[-1].block = block
                        
                # ----- OTHER and not equal: we create a new block
                        
                else:
                    if line_type == 'ORDERED':
                        prefix = "1. "
                        
                    block = Text(parent=stack[-2].parent, prefix=prefix)
                    block.add_lines(line)
                    stack[-1].block = block
                    
            else:
                if line_type == "ORDERED":
                    prefix = "1. "
                
                # ----- Indentation can be deeper or shallower
                
                deeper = indent > stack[-1].indent
                
                # ----- If deeper, create a child of the top of stack
                
                if deeper:
                    block = Text(parent=stack[-1].block, prefix=prefix)
                    
                # ----- otherwise pop the stack
                
                else:
                    # Back in the stack
                    
                    while stack[-1].indent >= indent:
                        stack.pop()

                    block = Text(parent=stack[-1].block, prefix=prefix)
                        
                # ----- stack and add the line
                    
                block.add_lines(line)
                stack.append(Stacker(block, indent, line_type, order=1))
                
        # ---------------------------------------------------------------------------
        # Create the sub sections
        
        stack = [(-1, self)] # Another stack
        
        for index, title in enumerate(titles):
            
            level = levels[index]
            
            if level == stack[-1][0]:
                section = Section(stack[-2][1], title)
                stack[-1] = (level, section)
                
            elif level > stack[-1][0]:
                for i in range(stack[-1][0], level-1):
                    stack.append((i, Section(stack[-1][1])))
                
                section = Section(stack[-1][1], title)
                stack.append((level, section))
                
            else:
                for i in range(level, stack[-1][0]+1):
                    stack.pop()

                section = Section(stack[-1][1], title)
                stack.append((level, section))
                
            section.set_text(texts[index+1])
            
    # ------------------------------------------------------------------------------------------
    # Text generation
        
    def gen_text(self):
        indent = self.text_indent
        
        if self.title is not None:
            yield f"\n{indent}{self.title}"
            yield f"{indent}{'-'*len(self.title)}"
        
        for line in super().gen_text():
            yield line
            
    # ------------------------------------------------------------------------------------------
    # Markdown output
        
    def gen_md(self):

        if self.title is not None:
            yield f"\n{'#' * (self.depth+1)} {self.title}\n"

        for line in super().gen_md():
            yield line
            
# ----------------------------------------------------------------------------------------------------
# Doc: a Section with generations commmands
            
            
class Doc(Section):
    def __init__(self):
        super().__init__()
        self.base_indent = "    "
        self.references = {}
        self.md_root    = ""
        self.md_images_ = "images/" # Relative to root
        
    @property
    def images_path(self):
        if self.md_images_[0] == "/":
            return self.md_images_
        else:
            return self.md_root + self.md_images_
    
        
    def solve_link(self, link):
        
        words = link.split(":")
        if len(words) == 1:
            return link
        
        words[0] = words[0].strip()
        words[1] = words[1].strip()
        
        
        if words[0].lower() == 'ref':
            solved = self.references.get(words[1])
            if solved is None:
                raise RuntimeError(f"Link error in : '{link}'': The reference '{words[1]}' doesn't exist:\n{self.references}")
            return solved
        
        if words[0].lower() == 'section':
            section = self.get_section(words[1])
            if section is None:
                raise RuntimeError(f"Link error in : '{link}'': The section path '{words[1]}' doesn't exist:\n{self.tree()}")
                
        if words[0].lower() in ['image', 'img']:
            return self.images_path + words[1]
                
        return link
            
            
            
            
            
            
            
            
            
text = """
        Introduction text
        
        See: [The link](ref:foo) or [toto](ref:  python   ), image = ![Image](image.png)
        See: <img src="toto.png"> or [toto](ref:python), image = ![Image](image.png)
        
        
        Arguments
        =========
            - self
            - factor: float
              Factor comment
              
        Sub section
        -----------
            I'm here
            
                
        Returns
        -------
            - Float
            
              See [Sub](section:Arguments.Sub section)
        """
        
doc = Doc()
doc.references["foo"] = "Bar"
doc.references["python"] = "http://python.org"

doc.set_text(text)


if False:
    print()
    print("TEXT")
    print("----")
    for line in doc.gen_text():
        print(line)
    
if True:
    print()
    print("MARKDONW")
    print("--------")
    for line in doc.gen_md():
        print(line)


        
        