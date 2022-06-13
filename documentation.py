#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  3 16:40:15 2022

@author: alain.bernard@loreal.com
"""

import re
import logging
import pprint

logger = logging.getLogger()

# ----------------------------------------------------------------------------------------------------
# Utilities to remove a python source block ``` ... ``` from a text:
#
# tk, sources = tokenize_python(text)
# utk = untokenize_python(tk, sources)
#
# print("Back to initial text:", utk == text)
#

def tokenize_python(text):

    sources = {}
    def tokenize(m):
        
        key = f"PYTHON {len(sources)-1}"
        
        if False:
        # ----- source lines
            
            source = m.group(1)
            lines  = source.split("\n")
            while lines[0].strip() == "":
                lines.remove(lines[0])
    
            if lines[0].strip().startswith("```python"):
                strips     = [lines[0].strip()]
                lines[0]   = strips[0]
                
                indents    = [99]
                for i in range(1, len(lines)):
                    strips.append(lines[i].strip())
                    if strips[-1]:
                        indents.append(lines[i].find(strips[-1][0]))
                    else:
                        indents.append(99)
                        
                min_indent = min(indents)
    
                if min_indent < 99:
                    for i in range(1, len(lines)):
                        lines[i] = " " * (indents[i] - min_indent) + strips[i]
                
                source = "\n".join(["", ""] + lines)
            
            sources[key] = source
        
        else:
            sources[key] = m.group(1)
        
        
        return f"<<{key}>>"

    t = re.sub(r"(\s*```[^`]*```)", tokenize, text)
    return t, sources

def untokenize_python(text, sources):
    
    def back(m):
        try:
            return sources[m.group(1)]
        except Exception as e:
            print(f"Error when untokenizeing: {text}")
            print("sources:")
            pprint.pprint(sources)
            raise e

    return re.sub(r"\s*<<([^>]+)>>", back, text)


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
        
        s = f"{'    '*self.depth()}<{type(self).__name__}, blocks={len(self)}>\n"
        for block in self:
            s += repr(block)
        return s
    
    # ------------------------------------------------------------------------------------------
    # The depth of the block

    def depth(self, markdown=False):
        if markdown:
            if hasattr(self.md_file) and self.md_file is not None:
                return 0
            elif self.parent is None:
                return 0
            else:
                return self.parent.depth(True) + 1
        else:
            if self.parent is None:
                return 0
            else:
                return 1 + self.parent.depth(False)
        
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
    
    
    @property
    def max_width(self):
        doc = self.top
        return doc.text_width if isinstance(doc, Doc) else 100
    
    # ------------------------------------------------------------------------------------------
    # Text indentation for text output    
        
    def text_indent(self, markdown=False):
        doc = self.doc
        if markdown:
            indent = ""
            cur = self
            while cur is not None:
                cur = cur.parent
                if isinstance(cur, Text):
                    indent += "  "
                else:
                    return indent
            return indent
        else:
            return ("    " if doc is None else doc.base_indent) * self.depth(False)

    # ------------------------------------------------------------------------------------------
    # Text output
        
    def gen_text(self, markdown=False):
        for block in self:
            for line in block.gen_text(markdown=markdown):
                yield line
                
# ----------------------------------------------------------------------------------------------------
# Text: a list of lines
#
# The prefix is used for lists (- or 1.) and evidence (>)          
        
class Text(Block):
    
    def __init__(self, parent=None, prefix=None):
        super().__init__(parent)
        if prefix is None:
            self.prefix = ""
        elif prefix[-1] == " ":
            self.prefix = prefix
        else:
            self.prefix = prefix + " "
        
        self.lines  = []
        
    def __repr__(self):
        lines = [line[:10] for line in self.lines]
        s = f"{'    '*self.depth()}<Text, blocks: {len(self)}, lines: {len(self.lines)}, prefix='{self.prefix}'> {lines}\n"
        for block in self:
            s += repr(block)
        return s
        
    # ------------------------------------------------------------------------------------------
    # Add lines
    #
    # The sources is an optional dictionary used to restore the source code if removed
    # with tokenize_python
    
    def add_lines(self, *lines, sources=None):
        for line in lines:
            if sources is None:
                self.lines.append(line)
            else:
                for ul in untokenize_python(line, sources).split("\n"):
                    self.add_lines(ul)
            
    # ------------------------------------------------------------------------------------------
    # solve a link
    
    def solve_link(self, link):
        doc = self.doc
        return link if doc is None else doc.solve_link(link)

    # ------------------------------------------------------------------------------------------
    # Markdown output
        
    def gen_text(self, markdown=False):
        
        # ---------------------------------------------------------------------------
        # Markdown: replace a link by a solved link
        
        def solve(match):
            start = match.group(1)
            if start[0] == '!':
                return start + self.solve_link("image:" + match.group(2))
            else:
                return start + self.solve_link(match.group(2))
            
        def solve_src(match):
            return match.group(1) + self.solve_link("image:" + match.group(2))

        # ---------------------------------------------------------------------------
        # Text: suppress the link
        
        def suppress(match):
            return match.group(1)

        # ------------------------------------------------------------
        # Loop on the lines
        
        indent = self.text_indent(markdown)
        first  = True

        for line in self.lines:
            
            
            # ----- Solve the image links

            if markdown:

                # Markdown syntax
                
                line = re.sub(r"(!?\[[^\]]+\]\()([^)]+)", solve, line)
                
                # Html syntax
    
                line = re.sub(r'(<img\s+.*src\s*=\s*")([^"]+)', solve_src, line)
                
            else:
                line = re.sub(r"!?\[([^\]]+)\]\([^)]+\)", suppress, line)
            
            # ----- Output
            
            if first:
                yield f"{indent}{self.prefix}{line}"
                first = False
                indent += " " * len(self.prefix)
                    
            else:
                yield f"{indent}{line}"
                
        for line in super().gen_text(markdown):
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
        self.id    = None
        
        # ----- md properties
        
        self.md_folder_ = None
        self.md_file_   = None
        
    # ------------------------------------------------------------------------------------------
    # From doc parser
    
    @classmethod
    def FromParserDoc(cls, parent=None, prefix=None, pdoc=None):
        
        if not pdoc.is_class:
            if pdoc.comment.strip() == "":
                return None
        
        title = pdoc.name if prefix is None else f"{prefix} {pdoc.name}"
        section = cls(parent = parent, title=title)
        section.set_text(pdoc.comment)
        
        if pdoc.is_class:
            for pdef in pdoc.funcs.values():
                cls.FromParserDoc(parent=section, pdoc=pdef)
        return section

    # ------------------------------------------------------------------------------------------
    # Tag property  

    @staticmethod
    def build_tag(title):
        return None if title is None else title.lower().replace(' ', '-').replace('.', '_').replace(':', '')
    
    @property
    def tag(self):
        return Section.build_tag(self.title) if self.tag_ is None else self.tag_
    
    @tag.setter
    def tag(self, value):
        self.tag_ = value
        
    # ------------------------------------------------------------------------------------------
    # Add text
    
    def add_lines(self, *lines, prefix=None, sources=None):
        
        new = len(self) == 0 or prefix is not None
        if new:
            text = Text(self, prefix)
        else:
            text = self[-1]
            
        text.add_lines(*lines, sources=sources)
        
    # ------------------------------------------------------------------------------------------
    # Get the section md_file
    
    @property
    def md_file(self):
        if self.md_file_ is None:
            if self.parent is None:
                return ""
            else:
                return self.parent.md_file
        else:
            return self.md_file_
        
    @md_file.setter
    def md_file(self, value):
        self.md_file_ = value
        
    # ------------------------------------------------------------------------------------------
    # Get the section folder

    @property
    def md_folder(self):
        if self.md_folder_ is None:
            if self.parent is None:
                return ""
            else:
                return self.parent.md_folder
        else:
            return self.md_folder_
        
    @md_folder.setter
    def md_folder(self, value):
        self.md_folder_ = value
        
    # ------------------------------------------------------------------------------------------
    # Get the section path
    
    @property
    def md_path(self):
        if self.md_folder_ is None:
            if self.parent is None:
                return ""
            else:
                return self.parent.md_path
            
        elif self.parent is None:
            return f"{self.md_folder_}/"
        
        elif self.md_folder == "":
            return self.parent.md_path
        
        else:
            return f"{self.parent.md_path}{self.md_folder_}/"
        
    # ------------------------------------------------------------------------------------------
    # Get the link to the file
    
    @property
    def file_link(self):
        return self.md_path + self.md_file

    # ------------------------------------------------------------------------------------------
    # The the link to this section
    #
    # If from_section is defined, can return an anchor
    
    def url(self, from_section=None):
        file_link = self.file_link
        stag = f"#{self.tag}"
        if from_section is None or from_section.file_link != file_link:
            return file_link + stag
        else:
            return stag
        
    @property
    def md_depth(self):
        if self.md_file_ is None:
            if self.parent is None:
                return 0
            else:
                return self.parent.md_depth + 1
        else:
            return 0
        
    # ------------------------------------------------------------------------------------------
    # Access to the top section through path syntax:
    #
    # Classes reference.class Node.__init__ : section "__init__" in section "class Node" in "Classes reference"
        
    def get_section(self, section_id):
        
        if section_id == self.id:
            return self
        
        for section in self.get_sections():
            found = section.get_section(section_id)
            if found is not None:
                return found

        return None
    
    # ------------------------------------------------------------------------------------------
    # The sections
    
    def add_section(self, section):
        section.parent = self
        self.append(section)
        return section
    
    def get_sections(self, sort=False):
        sections = {}
        for block in self:
            if isinstance(block, Section):
                sections[block.tag] = block
                
        if sort:
            return [sections[k] for k in sorted(sections)]
        else:
            return list(sections.values())
    
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
    # Table of contents
    # Only mark down
    
    def gen_toc(self, depth=1, sort=False, classify=None, markdown=True):
        
        sections = self.get_sections(sort=sort)
        
        if classify is None:
            for section in sections:
                yield f"- [{section.title}](/{section.file_link})"
                if depth > 1:
                    for line in section.gen_toc(depth=depth-1, sort=sort):
                        yield "  " + line
            return
        
        classified = {}
        if isinstance(classify, str):
            attr = classify
        elif isinstance(classify, (list, tuple)) and len(classify) == 2:
            attr = classify[0]
            for v in classify[1]:
                classified[v] = []
        else:
            raise RuntimeError(f"Classify argument must be a string or a couple (string, list)")
        
        for section in sections:
            if hasattr(section, attr):
                name = getattr(self, attr)
            else:
                name = "Other"
                
            if classified.get(name) is None:
                classified[name] = [section]
            else:
                classified[name].append(section)
            
        for name, sects in classified:
            yield f"- {name}"
            for section in sects:
                yield f"  - [{section.title}](/{section.link_file})"
                if depth > 1:
                    for line in section.gen_toc(depth=depth-1, sort=sort, markdown=markdown):
                        yield "    " + line
        
    
    
    # ------------------------------------------------------------------------------------------
    # Tree of sections (for debug)
    
    def tree(self, mode=None):
        s = "    " * self.depth() + str(self.title) + "\n"
        for block in self:
            if isinstance(block, Section):
                s += block.tree(mode=mode)
        return s
    
    # ------------------------------------------------------------------------------------------
    # Initialization from text
    
    def set_text(self, text):
        
        # ----- Remove the source code blocks
        #
        # Once the text is split in sections and lines, the untokenization is made:
        #
        # - For the introductory text, when setting the lines:
        #   for line in texts[0]:
        #        ...
        #       block.add_lines(line, sources=sources)
        #
        # - For the sections texts, when sending the text to the section
        #   section.set_text(untokenize_python(texts[index+1], sources))
        #
        
        text, sources = tokenize_python(text)
        
        # ---------------------------------------------------------------------------
        # Split in sections
        
        txt_title_pat = re.compile(r"\s*(.+)\s*\n\s*([-=]+)\s*\n")
        md_title_pat  = re.compile(r"\n\s*(#+)\s(.*)")
        
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
    
            for match in md_title_pat.finditer("\n" + text):  # Add a leading \n because the md pattern searchs:  \n.....#
                
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
        # Untokenize the python source
        
        for i in range(len(texts)):
            texts[i] = untokenize_python(texts[i], sources)
        sources = None
        
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
                    stack[-1].block.add_lines(line, sources=sources)
                    
                # ----- OTHER but equal: we create an new block for lists
                    
                elif line_type == stack[-1].line_type:
                    
                    if line_type == 'EVIDENCE':
                        stack[-1].block.add_lines(line, sources=sources)
                    
                    else:
                        if line_type == 'ORDERED':
                            stack[-1].order += 1
                            prefix = f"{stack[-1].order}. "
                            
                        block = Text(parent=stack[-2].block, prefix=prefix)
                        block.add_lines(line, sources=sources)
                        stack[-1].block = block
                        
                # ----- OTHER and not equal: we create a new block
                        
                else:
                    if line_type == 'ORDERED':
                        prefix = "1. "
                        
                    block = Text(parent=stack[-2].block, prefix=prefix)
                    block.add_lines(line, sources=sources)
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
                    
                block.add_lines(line, sources=sources)
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
                
            section.set_text(untokenize_python(texts[index+1], sources))
            
    # ------------------------------------------------------------------------------------------
    # Text generation
        
    def gen_text(self, markdown=False):
        indent = self.text_indent(markdown)
        
        if self.title is not None:
            if markdown:
                title = self.title
                match = re.search("__(.+)__", title)
                if match is not None:
                    title = r"\_\_" + match.group(1) + r"\_\_"
                    
                yield f"\n{'#' * (self.md_depth+1)} {title}\n"
            else:
                yield "\n"
                yield f"{indent}{self.title}"
                yield f"{indent}{'-'*len(self.title)}"
        
        for line in super().gen_text(markdown):
            yield line
            
            
# ----------------------------------------------------------------------------------------------------
# Doc: a Section with generations commmands
            
            
class Doc(Section):
    def __init__(self):
        super().__init__()
        
        self.base_indent = "    "
        self.text_width  = 100
        
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
        
        algo   = words[0].strip().lower()
        
        ref    = words[1].strip().split('#')
        sid    = ref[0].strip()
        anchor = f"#{ref[1].lower().strip()}" if len(ref) == 2 else ""
        
        if algo == 'ref':
            solved = self.references.get(sid)
            if solved is None:
                logger.error(f"Link error in '{link}': The reference '{words[1]}' doesn't exist.")
            return solved + anchor
        
        if words[0].lower() == 'id':
            section = self.get_section(sid)
            if section is None:
                logger.error(f"Link error in : '{link}': The section named '{words[1]}' doesn't exist.\nDoc sections: {[section.title for section in self]}")
            return "/" + section.file_link + anchor
                
        if words[0].lower() in ['image', 'img']:
            return self.images_path + sid
        
        # Nothing
                
        return link
    
    
def debug():

    text= """ Test """

    doc = Doc()
    doc.set_text(text)
    
    if True:
        print()
        print("TEXT")
        print("----")
        for line in doc.gen_text():
            print(line)
        
    if True:
        print()
        print("MARKDONW")
        print("--------")
        for line in doc.gen_text(True):
            print(line)


#debug()        
        
