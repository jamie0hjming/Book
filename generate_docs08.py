#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C/C++ header documentation generator matching Doxygen 1.16.1 output.

Parses /** comments, @defgroup, enums, structs, classes, and functions
from .h/.hpp files, then generates HTML pages and CHM help files
that mirror Doxygen's exact styling and layout.
"""

import hashlib
import html as html_mod
import os
import re
import shutil
import subprocess
from collections import defaultdict, namedtuple
from pathlib import Path

# ────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────
PROJECT_NAME = "iSulad"
PROJECT_NUMBER = ""
PROJECT_BRIEF = "iSulad - Lightweight container runtime"
OUT_DIR = Path("docs") / "html"
DOXYGEN_REF = Path("..") / "123123" / "html"
SOURCE_DIRS = [Path("..") / "iSulad" / "src"]
CHM_FILE = Path("..") / "isulad_docs.chm"
HHC = r"C:\Program Files (x86)\HTML Help Workshop\hhc.exe"
PAGE_EXT = ".html"
ENCODING = "utf-8"


# ════════════════════════════════════════════════════════════════
# Helper utilities
# ════════════════════════════════════════════════════════════════

def esc(text):
    """HTML-escape text, handling None."""
    return html_mod.escape(text or "")


def file_id(filepath):
    """Convert file path to Doxygen page name.

    Pattern: constants.h -> constants_8h
    Doxygen convention: underscores become __ in page names.
    """
    name = filepath.name
    base = name.rsplit('.', 1)[0] if '.' in name else name
    ext = name.rsplit('.', 1)[1] if '.' in name else ""
    safe_base = base.replace('_', '__')
    return f"{safe_base}_8{ext}"


def section_header(title, anchor_id):
    """Return a Doxygen-style section header row."""
    return (f'<tr class="heading"><td colspan="2">'
            f'<h2 id="header-{anchor_id}" class="groupheader">'
            f'<a id="{anchor_id}" name="{anchor_id}"></a>'
            f'{title}</h2></td></tr>\n')


def highlight_code(escaped_text):
    """Apply syntax highlighting spans to HTML-escaped source code."""
    line = escaped_text
    # Comments (// to end of line)
    line = re.sub(r'(\/\/.*$)', r'<span class="comment">\1</span>',
                  line, flags=re.MULTILINE)
    # Comments (/* ... */)
    line = re.sub(r'(\/\*.*?\*\/)', r'<span class="comment">\1</span>',
                  line, flags=re.DOTALL)
    # Preprocessor directives
    pp = r'^(#\s*(?:include|define|ifdef|ifndef|endif|else|elif|pragma|error|warning)\b.*)'
    line = re.sub(pp, r'<span class="preprocessor">\1</span>',
                  line, flags=re.MULTILINE)
    # String literals
    line = re.sub(r'(&quot;(?:[^&]|&(?!quot;))*?&quot;)',
                  r'<span class="stringliteral">\1</span>', line)
    # Keywords
    kw = (r'\b(alignas|alignof|auto|bool|break|case|catch|class|const|'
          r'constexpr|continue|decltype|default|delete|do|double|else|'
          r'enum|explicit|export|extern|false|final|float|for|friend|'
          r'goto|if|inline|int|long|mutable|namespace|new|noexcept|'
          r'nullptr|operator|override|private|protected|public|register|'
          r'return|short|signed|sizeof|static|static_cast|struct|switch|'
          r'template|this|throw|true|try|typedef|typeid|typename|union|'
          r'unsigned|using|virtual|void|volatile|while)\b')
    parts = re.split(r'(<span[^>]*>|</span>)', line)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(kw, r'<span class="keyword">\1</span>', parts[i])
    return ''.join(parts)


# ════════════════════════════════════════════════════════════════
# Data classes
# ════════════════════════════════════════════════════════════════

class DocComment:
    """Parsed Doxygen comment block."""

    def __init__(self, raw=""):
        self.brief = ""
        self.details = ""
        self.return_ = ""
        self.retvals = []   # [(code, desc), ...]
        self.params = []    # [(direction, name, desc), ...]
        self.pre = ""
        self.post = ""
        self.note = ""
        self.warning = ""
        self.see = ""
        self.deprecated = ""
        self._parse(raw)

    def _parse(self, raw):
        text = raw.strip()
        if not text:
            return

        # Extract @brief
        m = re.search(r'@brief\s+(.*?)(?=\s*@|\s*$)', text, re.DOTALL)
        if m:
            self.brief = m.group(1).strip()

        # Extract @details
        m = re.search(r'@details\s+(.*?)(?=\s*@|\s*$)', text, re.DOTALL)
        if m:
            self.details = m.group(1).strip()

        # Extract @param
        for m in re.finditer(
                r'@param\s*\[?(\w*)\]?\s+(\w[\w_]*)\s+(.*?)(?=\s*@|\s*$)',
                text, re.DOTALL):
            direction = m.group(1) or "in"
            name = m.group(2)
            desc = m.group(3).strip()
            self.params.append((direction, name, desc))

        # Extract @return
        m = re.search(r'@return\s+(.*?)(?=\s*@|\s*$)', text, re.DOTALL)
        if m:
            self.return_ = m.group(1).strip()

        # Extract @retval
        for m in re.finditer(
                r'@retval\s+(\S+)\s+(.*?)(?=\s*@|\s*$)', text, re.DOTALL):
            self.retvals.append((m.group(1), m.group(2).strip()))

        # Extract @pre / @post / @note / @warning / @see / @deprecated
        for tag, attr in [('pre', 'pre'), ('post', 'post'),
                          ('note', 'note'), ('warning', 'warning'),
                          ('see', 'see'), ('deprecated', 'deprecated')]:
            m = re.search(rf'@{tag}\s+(.*?)(?=\s*@|\s*$)', text, re.DOTALL)
            if m:
                setattr(self, attr, m.group(1).strip())

    def has_content(self):
        """True if any documentation was parsed."""
        return bool(self.brief or self.details or self.return_ or self.params)


EnumValue = namedtuple("EnumValue", "name value doc")
StructField = namedtuple("StructField", "type name doc")
FuncParam = namedtuple("FuncParam", "type name direction doc")


class DocEntity:
    """A documented C/C++ entity."""

    def __init__(self, kind, name, doc=None):
        self.kind = kind          # "enum" | "struct" | "function" | ...
        self.name = name
        self.doc = doc or DocComment()
        self.raw_decl = ""
        self.func_return = ""
        self.func_params = []
        self.enum_values = []
        self.struct_fields = []

    def entity_id(self):
        """Stable HTML anchor based on kind + name."""
        clean = re.sub(r'[^a-zA-Z0-9_]', '_',
                       f"{self.kind}_{self.name}").lower()
        return clean[:64]


class FileInfo:
    """Information collected from a single header file."""
    def __init__(self, path):
        self.path = str(path)
        self.entities = []


# ════════════════════════════════════════════════════════════════
# Parser
# ════════════════════════════════════════════════════════════════

FUNC_SKIP = {"typedef", "if", "for", "while", "return", "switch", "case",
             "#define", "#include", "#if", "#ifdef", "#ifndef",
             "#else", "#endif"}
KIND_LABELS = {"struct": "结构体", "enum": "枚举", "function": "函数",
               "typedef": "类型定义", "define": "宏定义", "variable": "变量"}


class CParser:
    """Parse .h/.hpp files, extracting Doxygen-documented entities."""

    def __init__(self):
        self.files = {}          # path -> FileInfo
        self._current_file = None
        self._doc_accum = []
        self._in_doc_block = False
        self._in_skip_block = False
        self._pending_doc = None
        self._trailing_doc = ""
        self._accum_block = False
        self._accum_func = False

    # ── Entity creation ──

    def _add_entity(self, kind, name, decl_line):
        """Create an entity and attach it to the current file."""
        src = (self._pending_doc if not self._doc_accum and self._pending_doc
               else self._doc_accum)
        doc = DocComment("\n".join(src)) if src else DocComment()
        e = DocEntity(kind, name, doc)
        e.raw_decl = decl_line.strip()
        self._pending_doc = None
        if self._trailing_doc:
            if not doc.has_content():
                e.doc = DocComment(self._trailing_doc)
            self._trailing_doc = ""
        if self._current_file:
            self._current_file.entities.append(e)
        self._doc_accum = []
        return e

    # ── Finalizers ──

    def _finalize_enum(self, match, line):
        """Parse typedef enum { ... } name; into entity + values."""
        name = match.group(2) if match.lastindex >= 2 else ""
        e = self._add_entity("enum", name, line.strip())
        body = match.group(1) if match.lastindex >= 1 else ""
        # Strip C comments
        body = re.sub(r'/\*.*?\*/', '', body, flags=re.DOTALL)
        # Split by comma with brace-depth tracking
        parts = []
        cur = ""
        depth = 0
        for ch in body:
            if ch in '{(':
                depth += 1
                cur += ch
            elif ch in '})':
                depth -= 1
                cur += ch
            elif ch == ',' and depth == 0:
                parts.append(cur.strip())
                cur = ""
            else:
                cur += ch
        if cur.strip():
            parts.append(cur.strip())
        for p in parts:
            p = p.strip()
            if not p:
                continue
            vm = re.match(
                r'(\w[\w_]*)\s*(=\s*[^,]+?)?'
                r'\s*(?:\/\*\*\s*<\s*(.*?)\s*\*\/)?\s*$',
                p, re.DOTALL)
            if vm:
                vn = vm.group(1)
                vv = (vm.group(2) or "").strip().lstrip('= ')
                vd = (vm.group(3).strip()
                      if vm.lastindex >= 3 and vm.group(3) else "")
                e.enum_values.append(EnumValue(vn, vv, vd))
        return e

    def _finalize_struct(self, match, line):
        """Parse typedef struct { ... } name; into entity + fields."""
        name = match.group(2) if match.lastindex >= 2 else ""
        e = self._add_entity("struct", name, line.strip())
        body = match.group(1) if match.lastindex >= 1 else ""
        body = re.sub(r'/\*.*?\*/', '', body, flags=re.DOTALL)
        Field = namedtuple("Field", "type name doc")
        for part in body.split(';'):
            p = part.strip()
            if not p or p.startswith('#') or p.startswith('//'):
                continue
            doc = ""
            dm = re.search(r'/\*\*\s*<\s*(.*?)\s*\*/', p, re.DOTALL)
            if dm:
                doc = dm.group(1).strip()
                p = p[:dm.start()].strip()
            p = re.sub(r'//.*', '', p).strip()
            if p.startswith('struct ') or p.startswith('union '):
                continue
            # Function pointer: int (*name)(params)
            fp_m = re.match(r'(.*?)\s*\(\s*\*\s*(\w[\w_]*)\s*\)\(.*', p)
            if fp_m:
                ftype = fp_m.group(1).strip() + '(*)'
                fname = fp_m.group(2).strip()
                e.struct_fields.append(Field(ftype, fname, doc))
                continue
            # Skip non-pointer member functions
            if '(' in p and ')' in p:
                continue
            words = p.split()
            if len(words) >= 2:
                fn_candidate = words[-1].rstrip(';]')
                ftype = ' '.join(words[:-1])
                fname = fn_candidate
                while fname.startswith('*'):
                    ftype += '*'
                    fname = fname[1:]
                fname = fname.lstrip('*')
                if not fname:
                    fname = fn_candidate
                e.struct_fields.append(Field(ftype.strip(), fname, doc))
        return e

    def _parse_func(self, decl_line):
        """Parse a C/C++ function declaration."""
        decl = decl_line.strip().rstrip(';').strip()
        decl = re.sub(r'\s*=\s*(default|0)\s*', ' ', decl)
        decl = re.sub(r'\s+override\s*', ' ', decl)
        decl = re.sub(r'\s+final\s*', ' ', decl)
        decl = re.sub(r'\s+noexcept\s*', ' ', decl)
        decl = re.sub(r'\s+const\s+(?=\)|$)', ' ', decl)

        m = re.search(r'/\*\*\s*<\s*(.*?)\s*\*/', decl, re.DOTALL)
        trailing_doc = ""
        if m:
            trailing_doc = m.group(1).strip()
            decl = decl[:m.start()].strip()

        m = re.match(
            r'((?:\w[\w\s\*]*?))[\s\*]+(\w[\w_]*)\s*\(([^)]*)\)',
            decl)
        if not m:
            return None

        ret = m.group(1).strip()
        fname = m.group(2).strip()
        params_str = m.group(3) if m.lastindex >= 3 else ""

        e = self._add_entity("function", fname, decl_line.strip())
        e.func_return = ret
        if trailing_doc:
            e.doc = DocComment(trailing_doc)

        if params_str.strip() and params_str != "void":
            Param = namedtuple("Param", "type name direction doc")
            for part in params_str.split(','):
                p = part.strip()
                if not p:
                    continue
                # Name is the last identifier
                name_m = re.search(r'(\w[\w_]*)\s*$', p)
                pname = name_m.group(1) if name_m else p
                ptype = p[:name_m.start()].strip() if name_m else ""
                pdoc = ""
                direction = "in"
                for d, dn, desc in e.doc.params:
                    if dn == pname:
                        pdoc = desc
                        direction = d
                        break
                e.func_params.append(Param(ptype, pname, direction, pdoc))
        return e

    def _finalize_accum_block(self, line):
        """When a multi-line block closes, determine its type."""
        full = '\n'.join(self._accum_block[0])
        self._accum_block = False
        Field = namedtuple("Field", "type name doc")
        EV = namedtuple("EnumValue", "name value doc")

        # C-style: typedef enum { ... } name;
        m = re.match(
            r'typedef\s+enum\s*(?:\w+\s*)?\{(.*)\}\s*(\w[\w_]*)\s*;',
            full, re.DOTALL)
        if m:
            self._finalize_enum(m, line)
            return

        # C-style: typedef struct { ... } name;
        m = re.match(
            r'typedef\s+struct\s*(?:\w+\s*)?\{(.*)\}\s*(\w[\w_]*)\s*;',
            full, re.DOTALL)
        if m:
            self._finalize_struct(m, line)
            return

        # C++ style: enum Name { ... };
        m = re.match(r'enum\s+(\w[\w_]*)\s*\{(.*)\}', full, re.DOTALL)
        if m:
            e = self._add_entity("enum", m.group(1), line.strip())
            body_clean = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.DOTALL)
            for part in body_clean.replace('\n', '').split(','):
                p = part.strip()
                if not p:
                    continue
                vm = re.match(r'(\w[\w_]*)\s*(=\s*[^,]+)?', p)
                if vm:
                    e.enum_values.append(
                        EV(vm.group(1), (vm.group(2) or '').lstrip('= '), ''))
            return

        # C++ style: struct Name { ... };
        m = re.match(r'struct\s+(\w[\w_]*)\s*\{(.*)\}', full, re.DOTALL)
        if m:
            e = self._add_entity("struct", m.group(1), line.strip())
            body_clean = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.DOTALL)
            for part in body_clean.split(';'):
                p = part.strip()
                if not p or p.startswith('#') or p.startswith('//'):
                    continue
                p = re.sub(r'//.*', '', p).strip()
                # Function pointer
                fp_m = re.match(r'(.*?)\s*\(\s*\*\s*(\w[\w_]*)\s*\)\(.*', p)
                if fp_m:
                    e.struct_fields.append(
                        Field(fp_m.group(1).strip() + '(*)',
                              fp_m.group(2).strip(), ''))
                    continue
                if '(' in p and ')' in p:
                    continue
                words = p.split()
                if len(words) >= 2:
                    fn = words[-1].rstrip(';]')
                    ft = ' '.join(words[:-1])
                    while fn.startswith('*'):
                        ft += '*'
                        fn = fn[1:]
                    fn = fn.lstrip('*')
                    if not fn:
                        fn = words[-1].rstrip(';]')
                    e.struct_fields.append(Field(ft.strip(), fn, ''))
            return

    # ── Directive processing ──

    def _process_doc_directives(self):
        """Scan accumulated doc text for grouping directives."""
        text = "\n".join(self._doc_accum)
        if text.strip() and not any(
                kw in text for kw in
                ['@addtogroup', '@defgroup', '@}', '@{', '@file']):
            self._pending_doc = self._doc_accum.copy()
        self._doc_accum = []

    # ── Feed-line dispatchers ──

    def _try_block_comment(self, stripped):
        """Skip copyright banners (/***... but not /**)."""
        if not re.match(r'^/\*{3,}', stripped):
            return False
        if "*/" in stripped:
            return True
        self._in_skip_block = True
        return True

    def _try_end_skip_block(self, stripped):
        """End skip-block on */."""
        if not getattr(self, '_in_skip_block', False):
            return False
        if "*/" in stripped:
            self._in_skip_block = False
        return True

    def _try_trailing_doc(self, stripped):
        """Extract /**< trailing comments."""
        m = re.search(r'/\*\*<\s*(.*?)\s*\*/', stripped)
        if m:
            self._trailing_doc = m.group(1)
        return bool(m)

    def _try_doc_comment(self, stripped):
        """Process /** ... */ Doxygen doc blocks."""
        is_doc = re.match(r'^/\*\*(?:[^*]|$)', stripped)
        if not is_doc:
            return False
        # Single-line doc
        if "*/" in stripped and not stripped.startswith("/**<"):
            content = re.sub(r'^/\*\*\s*', '', stripped)
            content = re.sub(r'\s*\*/$', '', content)
            self._doc_accum.append(content)
            self._in_doc_block = False
            self._process_doc_directives()
            return True
        # Multi-line start
        self._doc_accum = []
        content = re.sub(r'^/\*\*\s*', '', stripped)
        if content and "*/" in content:
            content = content.replace("*/", "").strip()
            self._doc_accum.append(content)
            self._in_doc_block = False
            self._process_doc_directives()
            return True
        if content:
            self._doc_accum.append(content)
        self._in_doc_block = True
        return True

    def _try_doc_continuation(self, stripped):
        """Continuation inside multi-line /** ... */."""
        if not self._in_doc_block:
            return False
        if "*/" in stripped:
            content = re.sub(r'\s*\*/$', '', stripped)
            content = re.sub(r'^\s*\*\s?', '', content)
            if content:
                self._doc_accum.append(content)
            self._in_doc_block = False
            self._process_doc_directives()
        else:
            content = re.sub(r'^\s*\*\s?', '', stripped)
            if content:
                self._doc_accum.append(content)
        return True

    def _try_accum_continue(self, line, stripped):
        """Continue multi-line block (typedef/struct/enum) accumulation."""
        if not getattr(self, '_accum_block', False):
            return False
        self._accum_block[0].append(line)
        for ch in line:
            if ch == '{':
                self._accum_block[1] += 1
            elif ch == '}':
                self._accum_block[1] -= 1
        if self._accum_block[1] == 0:
            self._finalize_accum_block(line)
        return True

    def _try_start_accum(self, stripped, line):
        """Start accumulation for multi-line typedef/struct/enum."""
        patterns = [
            r'typedef\s+(?:enum|struct)\s*(?:\w+\s*)?\{',
            r'enum\s+\w+\s*\{',
            r'struct\s+\w+\s*\{',
        ]
        for kw in patterns:
            if (re.match(kw, stripped) and '};' not in stripped
                    and not stripped.endswith(';')):
                self._accum_block = [[line], 0]
                for ch in line:
                    if ch == '{':
                        self._accum_block[1] += 1
                    elif ch == '}':
                        self._accum_block[1] -= 1
                return True
        return False

    def _try_class(self, stripped, line):
        """Declare class (without accumulating body)."""
        m = re.match(r'class\s+(\w[\w_]*)', stripped)
        if m and stripped.endswith('{'):
            self._add_entity('class', m.group(1), line.strip())
            self._doc_accum = []
            return True
        return False

    def _try_typedef(self, stripped, line):
        """Single-line typedef."""
        m = re.match(r'typedef\s+enum\s*\{(.*?)\}\s*(\w[\w_]*)\s*;',
                     stripped, re.DOTALL)
        if m:
            self._finalize_enum(m, line)
            return True
        m = re.match(r'typedef\s+struct\s*\{(.*?)\}\s*(\w[\w_]*)\s*;',
                     stripped, re.DOTALL)
        if m:
            self._finalize_struct(m, line)
            return True
        m = re.match(
            r'typedef\s+(?!enum\s*\{)(?!struct\s*\{)(.+?)\s+(\w[\w_]*)\s*;',
            stripped)
        if m:
            self._add_entity("typedef", m.group(2), line.strip())
            self._doc_accum = []
            return True
        return False

    def _try_define(self, stripped, line):
        """#define MACRO [value]."""
        m = re.match(r'#\s*define\s+(\w[\w_]*)\s*(.*)', stripped)
        if m:
            name = m.group(1)
            val = (m.group(2) or '').strip()
            val = re.sub(r'\s*(//.*|/\*.*?\*/)', '', val).strip()
            e = self._add_entity("define", name, line.strip())
            e.func_return = val
            self._doc_accum = []
            return True
        return False

    def _try_const_var(self, stripped, line):
        """const/constexpr global variable."""
        m = re.match(
            r'(?:const|constexpr|static\s+const|const\s+static)'
            r'\s+(?:\w[\w\s\*]*)\s+(\w[\w_]*)\s*(?:=|{)',
            stripped)
        if m and '(' not in stripped:
            self._add_entity("variable", m.group(1), line.strip())
            self._doc_accum = []
            return True
        return False

    def _try_function(self, stripped, line):
        """Function declaration detection and parsing."""
        first = stripped.split()[0] if stripped.split() else ""

        # Multi-line function accumulation
        if getattr(self, '_accum_func', False):
            self._accum_func.append(line)
            if ');' in stripped or (stripped.endswith(')')
                                     and ')' in stripped):
                full = ' '.join(l.strip() for l in self._accum_func)
                self._accum_func = False
                e = self._parse_func(full)
                return bool(e)
            return True

        # Single-line function
        cond = (stripped and not stripped.startswith("#")
                and first not in FUNC_SKIP
                and not stripped.startswith(("//", "/*"))
                and "(" in stripped and ")" in stripped
                and not stripped.startswith("extern")
                and not stripped.startswith("struct "))
        if cond:
            e = self._parse_func(line)
            return bool(e)

        # Start multi-line accumulation
        cond2 = (stripped and not stripped.startswith("#")
                 and first not in FUNC_SKIP
                 and not stripped.startswith(("//", "/*"))
                 and "(" in stripped and ")" not in stripped
                 and not stripped.startswith("extern")
                 and not stripped.startswith("struct ")
                 and stripped.endswith(',') and '(' in stripped)
        if cond2:
            self._accum_func = [line]
            return True
        return False

    # ── Main dispatch ──

    def feed_line(self, line):
        """Dispatch one line of source code to the appropriate handler."""
        stripped = line.strip()
        if self._try_block_comment(stripped):
            return
        if self._try_end_skip_block(stripped):
            return
        self._try_trailing_doc(stripped)
        if self._try_doc_comment(stripped):
            return
        if self._try_doc_continuation(stripped):
            return
        if self._try_accum_continue(line, stripped):
            return
        if self._try_start_accum(stripped, line):
            return
        if self._try_class(stripped, line):
            return
        if self._try_typedef(stripped, line):
            return
        if self._try_define(stripped, line):
            return
        if self._try_const_var(stripped, line):
            return
        if self._try_function(stripped, line):
            return
        # Default: clear doc accumulator if not building a doc
        if stripped and not stripped.startswith(("//", "/*")):
            if not self._in_doc_block:
                self._doc_accum = []

    def parse_file(self, filepath):
        """Parse a single header file."""
        self._current_file = FileInfo(filepath)
        self._doc_accum = []
        self._pending_doc = None
        self._in_doc_block = False
        self._in_skip_block = False
        self._trailing_doc = ""
        self._accum_block = False
        self._accum_func = False
        try:
            with open(filepath, encoding='utf-8', errors='replace') as f:
                for line in f:
                    self.feed_line(line)
        except Exception as e:
            print(f"  ⚠ Error parsing {filepath}: {e}")
        self.files[str(filepath)] = self._current_file


# ════════════════════════════════════════════════════════════════
# HTML page templates
# ════════════════════════════════════════════════════════════════

def page_doctype():
    return ('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 '
            'Transitional//EN" "https://www.w3.org/TR/xhtml1/DTD/'
            'xhtml1-transitional.dtd">\n'
            '<!-- 制作者 Doxygen 1.16.1 -->')


def page_head(title):
    return ('''<html xmlns="http://www.w3.org/1999/xhtml" lang="zh">
<head>
<meta http-equiv="Content-Type" content="text/xhtml;charset=UTF-8"/>
<meta http-equiv="X-UA-Compatible" content="IE=11"/>
<meta name="generator" content="Doxygen 1.16.1"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>''' + f'{PROJECT_NAME}: {esc(title)}' + '''</title>
<link href="tabs.css" rel="stylesheet" type="text/css"/>
<script type="text/javascript" src="jquery.js"></script>
<script type="text/javascript" src="dynsections.js"></script>
<link href="doxygen.css" rel="stylesheet" type="text/css" />
</head>
<body>
<script type="text/javascript">
$(function() { codefold.init(); });
</script>
''')


def page_titlebar():
    num = (f'<span id="projectnumber">&#160;{esc(PROJECT_NUMBER)}</span>'
           if PROJECT_NUMBER else '')
    brief = (f'<div id="projectbrief">{esc(PROJECT_BRIEF)}</div>'
             if PROJECT_BRIEF else '')
    return f'''<div id="top">
<div id="titlearea">
<table cellspacing="0" cellpadding="0">
 <tbody>
 <tr id="projectrow">
  <td id="projectalign">
   <div id="projectname">{esc(PROJECT_NAME)}{num}</div>
   {brief}
  </td>
 </tr>
 </tbody>
</table>
</div>
'''


def page_footer():
    return ('''<hr class="footer"/><address class="footer"><small>
Generated by&#160;<a href="https://www.doxygen.org/index.html">
<img class="footer" src="doxygen.svg" width="104" height="31"
alt="doxygen"/></a> 1.16.1
</small></address>
</div><!-- doc-content -->
</body></html>''')


def _dropdown_style():
    """Shared style for nav dropdowns."""
    return ('position:absolute;top:36px;left:0;background:white;'
            'border:1px solid #C4CFE5;border-radius:4px;'
            'box-shadow:0 2px 8px rgba(0,0,0,0.1);'
            'z-index:200;min-width:160px;padding:4px 0;')


def _sub_link(href, label):
    return (f'<a href="{href}" style="display:block;padding:4px 16px;'
            f'text-decoration:none;color:#283A5D;white-space:nowrap;'
            f'font-size:13px;">{label}</a>')


def nav_tabs(active_page="main"):
    """Top navigation bar with dropdown menus."""

    def li(page, label):
        cls = ' class="current"' if page == active_page else ''
        href = {"main": "index.html", "topics": "modules.html",
                "classes": "annotated.html",
                "files": "files.html", "pages": "pages.html"}.get(
                    page, "index.html")
        return f'<li{cls}><a href="{href}"><span>{label}</span></a></li>'

    # Classes dropdown
    classes_current = ' class="current"' if active_page == "classes" else ''
    classes_items = [
        ("annotated.html", "结构体"),
        ("classes.html", "结构体索引"),
        ("", "───"),
        ("globals_enum.html", "枚举"),
        ("globals_defs.html", "宏定义"),
    ]
    classes_html = ""
    for href, label in classes_items:
        if label.startswith("─"):
            classes_html += ('<div style="border-top:1px solid '
                             '#C4CFE5;margin:4px 0;"></div>\n')
        else:
            classes_html += _sub_link(href, label) + "\n"

    classes_tab = (
        f'<li{classes_current} style="position:relative;"'
        f' onmouseover="document.getElementById(\'cdd\').style.display'
        f'=\'block\';"'
        f' onmouseout="document.getElementById(\'cdd\').style.display'
        f'=\'none\';">'
        f'<a href="annotated.html"><span>结构体</span></a>'
        f'<div id="cdd" style="display:none;{_dropdown_style()}">'
        f'{classes_html}</div></li>')

    # Files dropdown
    files_current = ' class="current"' if active_page == "files" else ''
    files_items = [
        ("files.html", "文件列表"),
        ("", "───"),
        ("globals.html", "全局定义 - 全部"),
        ("globals_func.html", "全局定义 - 函数"),
        ("globals_type.html", "全局定义 - 类型定义"),
        ("globals_enum.html", "全局定义 - 枚举"),
        ("globals_eval.html", "全局定义 - 枚举值"),
        ("globals_defs.html", "全局定义 - 宏定义"),
        ("globals_vars.html", "全局定义 - 变量"),
    ]
    files_html = ""
    for href, label in files_items:
        if label.startswith("─"):
            files_html += ('<div style="border-top:1px solid '
                           '#C4CFE5;margin:4px 0;"></div>\n')
        else:
            files_html += _sub_link(href, label) + "\n"

    files_tab = (
        f'<li{files_current} style="position:relative;"'
        f' onmouseover="document.getElementById(\'fdd\').style.display'
        f'=\'block\';"'
        f' onmouseout="document.getElementById(\'fdd\').style.display'
        f'=\'none\';">'
        f'<a href="files.html"><span>文件</span></a>'
        f'<div id="fdd" style="display:none;{_dropdown_style()}'
        f'min-width:180px;">{files_html}</div></li>')

    return ('''<div id="main-nav">
  <div id="navrow1" class="tabs">
    <ul class="tablist">
''' + li("main", "首页") + '\n' + li("pages", "相关页面") + '\n'
        + classes_tab + '\n' + files_tab + '''
    </ul>
  </div>
</div>
</div><!-- top -->
''')


# ════════════════════════════════════════════════════════════════
# HTML Generator
# ════════════════════════════════════════════════════════════════

class HtmlGenerator:
    """Generate all HTML pages from parsed file data."""

    def __init__(self, parsed_files, out_dir):
        self.files = parsed_files
        self.out = Path(out_dir)
        self.out.mkdir(parents=True, exist_ok=True)

    def _file_page_name(self, filepath):
        return file_id(Path(filepath)) + PAGE_EXT

    def _entity_hash(self, name):
        """MD5-based anchor like Doxygen (a<32hex>)."""
        h = hashlib.md5(name.encode()).hexdigest()[:32]
        return 'a' + h

    def _entity_page_name(self, entity, ns=''):
        """Generate filename for a standalone entity page."""
        prefix = entity.kind
        qname = (ns + '::' + entity.name) if ns else entity.name
        safe = qname.replace('::', '_1_1')
        return f'{prefix}_{safe}{PAGE_EXT}'

    def _entity_page(self, type_name):
        """Find entity page URL for a type name."""
        for finfo in self.files.values():
            for e in finfo.entities:
                if e.name == type_name:
                    return self._entity_page_name(e)
        return None

    def _type_link(self, type_name):
        """HTML for a type reference, linked if entity page exists."""
        base = type_name.rstrip('*').rstrip()
        page = self._entity_page(type_name) or self._entity_page(base)
        if page:
            return f'<a class="el" href="{page}">{esc(type_name)}</a>'
        return esc(type_name)

    def _real_includes(self, fpath):
        """Extract #include lines from source file."""
        includes = []
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    m = re.match(r'\s*#\s*include\s+([<"])(.+?)[>"]', line)
                    if m:
                        includes.append((m.group(1), m.group(2)))
        except Exception:
            pass
        return includes[:20]

    # ── Directory tree ──

    def _dir_id(self, dir_path):
        h = hashlib.md5(str(dir_path).lower().encode()).hexdigest()[:32]
        return f"dir_{h}"

    def _build_dir_tree(self):
        """Build nested directory structure from parsed file paths."""
        root = {"name": "iSulad", "path": "iSulad",
                "subdirs": {}, "files": [],
                "id": self._dir_id("iSulad")}
        for fpath in sorted(self.files.keys()):
            fp = Path(fpath)
            parts = fp.parts
            try:
                start = next(i for i, p in enumerate(parts) if p == "iSulad")
            except StopIteration:
                start = 0
            node = root
            for i in range(start, len(parts) - 1):
                p = parts[i]
                dp = "/".join(parts[start:i + 1])
                if p not in node["subdirs"]:
                    node["subdirs"][p] = {
                        "name": p, "path": dp,
                        "subdirs": {}, "files": [],
                        "id": self._dir_id(dp), "parent": node}
                node = node["subdirs"][p]
            node["files"].append(fp)
        return root

    def _render_tree_rows(self, node, depth=0, row=0, pid=""):
        h = ""
        rid = f"{pid}{row}_"
        indent = depth * 16
        oe = "even" if row % 2 == 0 else "odd"
        has_kids = bool(node["subdirs"] or node["files"])
        if has_kids:
            arrow = (f'<span id="arr_{rid}" class="arrow" '
                     f'onclick="dynsection.toggleFolder(\'{rid}\')">'
                     f'<span class="arrowhead opened"></span></span>')
            icon = (f'<span id="img_{rid}" class="iconfolder" '
                    f'onclick="dynsection.toggleFolder(\'{rid}\')">'
                    f'<div class="folder-icon open"></div></span>')
        else:
            arrow = '<span style="width:16px;display:inline-block;">&#160;</span>'
            icon = arrow
        h += (f'<tr id="row_{rid}" class="{oe}"><td class="entry">'
              f'<span style="width:{indent}px;display:inline-block;">'
              f'&#160;</span>{arrow}{icon}'
              f'<a class="el" href="{node["id"]}{PAGE_EXT}" '
              f'target="_self">{esc(node["name"])}</a>'
              f'</td><td class="desc"></td></tr>\n')
        ci = 0
        for sd in sorted(node["subdirs"].values(), key=lambda x: x["name"]):
            h += self._render_tree_rows(sd, depth + 1, ci, rid)
            ci += 1
        for f in sorted(node["files"]):
            fid = file_id(f)
            fb = ""
            fs = str(f)
            if fs in self.files and self.files[fs].entities:
                fb = self.files[fs].entities[0].doc.brief or ""
            cid = f"{rid}{ci}"
            coe = "even" if ci % 2 == 0 else "odd"
            ci += 1
            h += (f'<tr id="row_{cid}" class="{coe}"><td class="entry">'
                  f'<span style="width:{(depth + 1) * 16}px;'
                  f'display:inline-block;">&#160;</span>'
                  f'<span style="width:16px;display:inline-block;">&#160;</span>'
                  f'<span class="icon"><div class="file-icon"></div></span>'
                  f'<a class="el" href="{fid}{PAGE_EXT}">{esc(f.name)}</a>'
                  f'</td><td class="desc">{esc(fb[:120]) if fb else ""}'
                  f'</td></tr>\n')
        return h

    # ── Page rendering methods ──

    def render_index_page(self):
        path = self.out / "index.html"
        c = page_doctype() + page_head(PROJECT_NAME)
        c += page_titlebar() + nav_tabs("main")
        c += f'''<div id="doc-content">
<div class="header"><div class="headertitle"><div class="title">
{esc(PROJECT_NAME)} </div></div></div>
<div class="contents">
<div class="textblock"><p>{esc(PROJECT_BRIEF)}</p>
<h1>概述</h1>
<p>iSulad 是一个轻量级容器运行时。</p>
<h1>模块</h1>
<p>源码组织在以下目录中:</p>
<ul>
<li><code>api/</code> - API 定义</li>
<li><code>client/</code> - 客户端库</li>
<li><code>cmd/</code> - 命令行工具</li>
<li><code>common/</code> - 公共工具</li>
<li><code>daemon/</code> - 守护进程</li>
<li><code>utils/</code> - 工具函数</li>
</ul>
</div>''' + page_footer()
        path.write_text(c, encoding='utf-8')

    def render_files_page(self):
        root = self._build_dir_tree()
        c = page_doctype() + page_head("文件列表")
        c += page_titlebar() + nav_tabs("files")
        c += '''<div id="doc-content">
<div class="header"><div class="headertitle"><div class="title">
文件列表</div></div></div>
<div class="contents">
<div class="textblock">这里列出了所有文件，并附带简要说明:</div>
<div class="directory">
<div class="levels">[详情级别
<span onclick="javascript:dynsection.toggleLevel(1);">1</span>
<span onclick="javascript:dynsection.toggleLevel(2);">2</span>
<span onclick="javascript:dynsection.toggleLevel(3);">3</span>
<span onclick="javascript:dynsection.toggleLevel(4);">4</span>
<span onclick="javascript:dynsection.toggleLevel(5);">5</span>
<span onclick="javascript:dynsection.toggleLevel(6);">6</span>
<span onclick="javascript:dynsection.toggleLevel(7);">7</span>
<span onclick="javascript:dynsection.toggleLevel(8);">8</span>
<span onclick="javascript:dynsection.toggleLevel(9);">9</span>
<span onclick="javascript:dynsection.toggleLevel(10);">10</span>]</div>
<table class="directory">
'''
        c += self._render_tree_rows(root)
        c += '''</table></div></div>''' + page_footer()
        self.out.joinpath("files.html").write_text(c, encoding='utf-8')

    def render_dir_pages(self):
        """Generate dir_*.html pages."""
        def walk(node):
            did = node["id"]
            parts = node["path"].replace("\\", "/").split("/")
            title = "/".join(parts[-3:]) if len(parts) >= 3 else node["name"]
            c = page_doctype() + page_head(f"{title} Directory Reference")
            c += page_titlebar() + nav_tabs("files")
            c += '<div id="nav-path" class="navpath"><ul>'
            for i in range(len(parts)):
                dp = "/".join(parts[:i + 1])
                c += (f'<li class="navelem"><a href="{self._dir_id(dp)}'
                      f'{PAGE_EXT}">{esc(parts[i])}</a></li>')
            c += '</ul></div></div><!-- top -->'
            c += (f'<div id="doc-content"><div class="header">'
                  f'<div class="headertitle"><div class="title">'
                  f'{esc(node["name"])} Directory Reference'
                  f'</div></div></div><div class="contents">\n')
            if node["subdirs"]:
                c += ('<table class="memberdecls"><tr class="heading">'
                      '<td colspan="2"><h2 id="header-subdirs" '
                      'class="groupheader"><a id="subdirs" '
                      'name="subdirs"></a>Directories</h2></td></tr>\n')
                for sd in sorted(node["subdirs"].values(),
                                 key=lambda x: x["name"]):
                    c += (f'<tr class="memitem:{sd["name"]}">'
                          f'<td class="memItemLeft">'
                          f'<span class="iconfolder">'
                          f'<div class="folder-icon"></div></span>'
                          f'&#160;</td><td class="memItemRight">'
                          f'<a class="el" href="{sd["id"]}{PAGE_EXT}">'
                          f'{esc(sd["name"])}</a></td></tr>\n')
                c += '</table>\n'
            if node["files"]:
                c += ('<table class="memberdecls"><tr class="heading">'
                      '<td colspan="2"><h2 class="groupheader">'
                      'Files</h2></td></tr>\n')
                for f in sorted(node["files"]):
                    fid = file_id(f)
                    fb = ""
                    fs = str(f)
                    if fs in self.files and self.files[fs].entities:
                        fb = self.files[fs].entities[0].doc.brief or ""
                    c += (f'<tr class="memitem:{fid}"><td class="memItemLeft">'
                          f'file &#160;</td><td class="memItemRight">'
                          f'<a class="el" href="{fid}{PAGE_EXT}">'
                          f'{esc(f.name)}</a></td></tr>\n')
                    if fb:
                        c += (f'<tr class="memdesc:{fid}">'
                              f'<td class="mdescLeft">&#160;</td>'
                              f'<td class="mdescRight">'
                              f'{esc(fb[:120])}<br/></td></tr>\n')
                c += '</table>\n'
            c += '</div>' + page_footer()
            (self.out / f"{did}{PAGE_EXT}").write_text(c, encoding='utf-8')
            for sd in node["subdirs"].values():
                walk(sd)
        walk(self._build_dir_tree())

    def render_file_page(self, fpath):
        """Generate a file documentation page."""
        finfo = self.files[fpath]
        fp = Path(fpath)
        page_name = self._file_page_name(fpath)
        path = self.out / page_name
        src_name = page_name.replace('.html', '_source.html')

        try:
            s = str(fpath).replace('\\', '/')
            idx = s.index("iSulad/src/")
            rel_path = s[idx:]
            dir_parts = rel_path.split('/')[:-1]
        except ValueError:
            rel_path = fp.name
            dir_parts = [fp.name]

        dir_ids = []
        for i in range(1, len(dir_parts) + 1):
            dp = "/".join(dir_parts[:i])
            dir_ids.append((dir_parts[i - 1], self._dir_id(dp)))

        c = page_doctype()
        c += page_head(fp.name)
        c += page_titlebar()
        c += nav_tabs("files")
        c += '<div id="nav-path" class="navpath"><ul>'
        for name, did in dir_ids:
            c += (f'<li class="navelem"><a href="{did}{PAGE_EXT}">'
                  f'{esc(name)}</a></li>')
        c += (f'<li class="navelem"><a class="el" href="#">'
              f'{esc(fp.name)}</a></li>')
        c += '</ul></div></div><!-- top -->'
        c += '<div id="doc-content">\n'

        # Summary bar
        by_kind = {}
        for e in finfo.entities:
            by_kind.setdefault(e.kind, []).append(e)
        summary_links = []
        kind_order = ["struct", "enum", "function", "typedef",
                       "define", "variable"]
        kind_anchors = {"struct": "struct-members", "enum": "enum-members",
                        "function": "func-members",
                        "typedef": "typedef-members",
                        "define": "define-members",
                        "variable": "var-members"}
        for kind in kind_order:
            if kind in by_kind:
                summary_links.append(
                    f'<a href="#{kind_anchors[kind]}">'
                    f'{KIND_LABELS[kind]}</a>')
        summary_bar = ' | '.join(summary_links) + '\n  ' if summary_links else ''

        c += (f'<div class="header">\n  <div class="summary">\n'
              f'{summary_bar}</div>\n'
              f'  <div class="headertitle"><div class="title">'
              f'{esc(fp.name)}</div></div>\n'
              f'</div><!--header-->\n'
              f'<div class="contents">\n')

        # Include directives
        raw_includes = self._real_includes(fpath)
        if raw_includes:
            c += '<div class="textblock">'
            for delim, inc in raw_includes:
                linked = False
                inc_norm = inc.replace('/', '\\')
                for fkey in self.files:
                    if fkey.endswith(inc) or fkey.endswith(inc_norm):
                        src = self._file_page_name(fkey).replace(
                            PAGE_EXT, '_source' + PAGE_EXT)
                        od = '&lt;' if delim == '<' else '&quot;'
                        cd = '&gt;' if delim == '<' else '&quot;'
                        c += (f'<code>#include {od}<a class="el" '
                              f'href="{src}">{esc(inc)}</a>{cd}</code>'
                              f'<br />\n')
                        linked = True
                        break
                if not linked:
                    od = '&lt;' if delim == '<' else '&quot;'
                    cd = '&gt;' if delim == '<' else '&quot;'
                    c += f'<code>#include {od}{esc(inc)}{cd}</code><br />\n'
            c += '</div>\n'

        # Source link
        c += f'<p><a href="{src_name}">浏览该文件的源代码.</a></p>\n'

        # Member tables
        for kind in kind_order:
            if kind not in by_kind:
                continue
            if kind == "struct":
                c += self._struct_table(by_kind[kind])
            elif kind == "enum":
                c += self._enum_table(by_kind[kind])
            elif kind == "function":
                c += self._function_table(by_kind[kind])
            elif kind == "typedef":
                c += self._typedef_table(by_kind[kind])
            elif kind in ("define", "variable"):
                c += self._simple_table(by_kind[kind], kind)

        # Function detail sections
        for e in by_kind.get("function", []):
            anchor = "r_f_" + e.name
            c += (f'<a name="doc-func-members" id="doc-func-members"></a>\n'
                  f'<a id="{anchor}" name="{anchor}"></a>\n'
                  f'<h2 class="memtitle"><span class="permalink">'
                  f'<a href="#{anchor}">&#9670;&#160;</a></span>'
                  f'{e.name}()</h2>\n'
                  f'<div class="memitem">\n<div class="memproto">\n'
                  f'      <table class="memname">\n        <tr>\n'
                  f'          <td class="memname">'
                  f'{esc(e.func_return)} {esc(e.name)} </td>\n'
                  f'          <td>(</td>\n')
            for i, p in enumerate(e.func_params):
                c += (f'          <td class="paramtype">'
                      f'{esc(p.type)}</td>\n'
                      f'          <td class="paramname">'
                      f'<em>{esc(p.name)}</em></td>\n')
                if i < len(e.func_params) - 1:
                    c += '          <td>,</td>\n'
            if not e.func_params:
                c += '          <td class="paramname">void</td>\n'
            c += ('          <td>)</td>\n        </tr>\n      </table>\n'
                  '</div><div class="memdoc">\n')
            if e.doc.brief:
                c += f"<p>{esc(e.doc.brief)}</p>\n"
            if e.func_params:
                c += ('<dl class="params"><dt>Parameters</dt><dd>\n'
                      '  <table class="params">\n')
                for p in e.func_params:
                    c += (f'    <tr><td class="paramname">'
                          f'{esc(p.name)}</td>'
                          f'<td>{esc(p.doc)}</td></tr>\n')
                c += '  </table>\n</dd></dl>\n'
            if e.doc.return_:
                c += (f'<dl class="section return"><dt>Returns</dt>'
                      f'<dd>{esc(e.doc.return_)}</dd></dl>\n')
            if e.doc.retvals:
                c += ('<dl class="retval"><dt>Return values</dt><dd>\n'
                      '  <table class="retval">\n')
                for code, desc in e.doc.retvals:
                    c += (f'    <tr><td class="paramname">'
                          f'{esc(code)}</td>'
                          f'<td>{esc(desc)}</td></tr>\n')
                c += '  </table>\n</dd></dl>\n'
            c += '</div></div>\n'

        c += page_footer()
        path.write_text(c, encoding='utf-8')

    def render_source_page(self, fpath):
        """Generate source code view page."""
        fp = Path(fpath)
        pname = self._file_page_name(fpath).replace(
            PAGE_EXT, "_source" + PAGE_EXT)
        doc_page = self._file_page_name(str(fpath))
        out_path = self.out / pname
        try:
            s = str(fpath).replace('\\', '/')
            idx = s.index("iSulad\\src\\") if "iSulad\\src\\" in str(fpath) else -1
            if idx < 0:
                idx = s.index("iSulad/src/")
            parts = s[idx:].split('/')[:-1]
        except Exception:
            parts = ["iSulad"]

        c = page_doctype() + page_head(fp.name + " source")
        c += page_titlebar() + nav_tabs("files")
        c += '<div id="nav-path" class="navpath"><ul>'
        for i in range(1, len(parts) + 1):
            dp = "/".join(parts[:i])
            c += (f'<li class="navelem"><a href="{self._dir_id(dp)}'
                  f'{PAGE_EXT}">{esc(parts[i - 1])}</a></li>')
        c += '</ul></div></div><!-- top -->'
        c += (f'<div id="doc-content"><div class="header">'
              f'<div class="headertitle"><div class="title">'
              f'{esc(fp.name)}</div></div></div>'
              f'<div class="contents">'
              f'<a href="{doc_page}">浏览该文件的文档.</a>'
              f'<div class="fragment">')
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as sf:
                for i, l in enumerate(sf.readlines()):
                    anchor = f"l{i + 1:05d}"
                    visible = f"{i + 1:5d}"
                    hl = highlight_code(esc(l.rstrip('\n\r')))
                    c += (f'<div class="line"><a id="{anchor}" '
                          f'name="{anchor}"></a>'
                          f'<span class="lineno"> {visible}</span> '
                          f'{hl}</div>\n')
        except Exception as ex:
            c += f'<p>Error: {ex}</p>'
        c += '</div></div>' + page_footer()
        out_path.write_text(c, encoding="utf-8")

    def render_classes_page(self):
        path = self.out / "annotated.html"
        items = []
        seen = set()
        for finfo in self.files.values():
            for e in finfo.entities:
                if e.kind not in ('struct', 'class', 'enum'):
                    continue
                if e.name in seen:
                    continue
                seen.add(e.name)
                page = self._entity_page_name(e)
                brief = e.doc.brief or ''
                items.append((e.name, e.kind, page, brief))
        items.sort(key=lambda x: x[0].lower())

        c = page_doctype() + page_head("结构体列表")
        c += page_titlebar() + nav_tabs("classes")
        c += (f'<div id="doc-content"><div class="header">'
              f'<div class="headertitle"><div class="title">结构体'
              f'</div></div></div>'
              f'<div class="contents">'
              f'<div class="textblock">这里列出了所有结构体，并附带简要说明:</div>'
              f'<div class="directory"><div class="levels">'
              f'[详情级别 <span onclick="javascript:dynsection.toggleLevel(1);">'
              f'1</span><span onclick="javascript:dynsection.toggleLevel(2);">'
              f'2</span>]</div><table class="directory">')
        for i, (name, kind, page, brief) in enumerate(items):
            oe = "even" if i % 2 == 0 else "odd"
            icon = {'struct': 'S', 'class': 'C', 'enum': 'E'}.get(kind, '?')
            c += (f'<tr id="row_{i}_" class="{oe}"><td class="entry">'
                  f'<span style="width:16px;display:inline-block;">&#160;</span>'
                  f'<span class="icona"><span class="icon">{icon}</span></span>'
                  f'<a class="el" href="{page}" target="_self">'
                  f'{esc(name)}</a>'
                  f'</td><td class="desc">'
                  f'{esc(brief[:200]) if brief else ""}</td></tr>\n')
        c += '</table></div></div>' + page_footer()
        path.write_text(c, encoding='utf-8')

    def render_class_index_page(self):
        path = self.out / "classes.html"
        by_letter = defaultdict(list)
        seen = set()
        for finfo in self.files.values():
            for e in finfo.entities:
                if e.kind not in ('struct', 'class', 'enum'):
                    continue
                if e.name in seen:
                    continue
                seen.add(e.name)
                letter = (e.name[0].upper()
                          if e.name and e.name[0].isalpha() else '_')
                by_letter[letter].append(
                    (e.name, e.kind, self._entity_page_name(e)))
        for k in by_letter:
            by_letter[k].sort(key=lambda x: x[0].lower())

        c = page_doctype() + page_head("结构体索引")
        c += page_titlebar() + nav_tabs("classes")
        letters = sorted(by_letter.keys(), key=lambda x: (x == '_', x))
        letter_links = ''.join(
            f'<li><a href="#index_{l.lower()}"><span>{l}</span></a></li>'
            for l in letters)
        c += (f'<div id="navrow4" class="tabs3">'
              f'<ul class="tablist">{letter_links}</ul></div>'
              f'<div id="doc-content"><div class="header">'
              f'<div class="headertitle"><div class="title">结构体索引'
              f'</div></div></div>'
              f'<div class="contents"><div class="textblock">'
              f'<p>这里列出了所有结构体索引:</p></div>')
        for letter in letters:
            c += (f'<h2><a class="anchor" id="index_{letter.lower()}">'
                  f'</a>{letter}</h2><table class="memberdecls">')
            for name, kind, page in by_letter[letter]:
                icon = {'struct': 'S', 'class': 'C', 'enum': 'E'}.get(
                    kind, '?')
                c += (f'<tr><td class="memItemLeft">'
                      f'<span class="icona"><span class="icon">'
                      f'{icon}</span></span>&#160;</td>'
                      f'<td class="memItemRight"><a class="el" href="{page}">'
                      f'{esc(name)}</a></td></tr>\n')
            c += '</table>'
        c += '</div>' + page_footer()
        path.write_text(c, encoding='utf-8')

    def render_pages_page(self):
        path = self.out / "pages.html"
        c = page_doctype() + page_head("相关页面")
        c += page_titlebar() + nav_tabs("pages")
        c += ('''<div id="doc-content">
<div class="header"><div class="headertitle"><div class="title">
相关页面</div></div></div>
<div class="contents">
<div class="textblock"><p><a href="index.html">Main Page</a></p></div>'''
              + page_footer())
        path.write_text(c, encoding='utf-8')

    def render_entity_page(self, entity, finfo):
        """Generate standalone entity detail page."""
        pname = self._entity_page_name(entity)
        path = self.out / pname
        fpath = getattr(finfo, 'path', None)
        fname = fpath.name if fpath else entity.name
        inc_name = file_id(fpath) + PAGE_EXT if fpath else ""
        src_page = inc_name.replace(PAGE_EXT, "_source" + PAGE_EXT)

        c = page_doctype() + page_head(
            f"{entity.name} {entity.kind.title()} Reference")
        c += page_titlebar() + nav_tabs("classes")
        c += (f'<div id="nav-path" class="navpath"><ul>'
              f'<li class="navelem"><a class="el" href="{pname}">'
              f'{esc(entity.name)}</a></li>'
              f'</ul></div></div><!-- top -->')
        summary = ('<a href="#pub-attribs">成员变量</a>'
                   if (entity.kind == 'struct' and entity.struct_fields)
                   or entity.enum_values else '')
        c += (f'<div id="doc-content"><div class="header">'
              f'  <div class="summary">{summary}</div>'
              f'  <div class="headertitle"><div class="title">'
              f'{esc(entity.name)}{{"struct":"结构体","enum":"枚举",'
              f'"class":"类"}.get(entity.kind, entity.kind.title())}'
              f' 参考</div></div></div><!--header-->'
              f'<div class="contents">')
        if inc_name:
            c += (f'<p><code>#include &lt;<a class="el" href="{inc_name}">'
                  f'{esc(fname)}</a>&gt;</code></p>')

        c += '<table class="memberdecls">'
        if entity.kind == 'struct' and entity.struct_fields:
            c += ('<tr class="heading"><td colspan="2">'
                  '<h2 id="header-pub-attribs" class="groupheader">'
                  '<a id="pub-attribs" name="pub-attribs"></a>成员变量'
                  '</h2></td></tr>')
            for fld in entity.struct_fields:
                fhash = self._entity_hash(entity.name + '::' + fld.name)
                thtml = self._type_link(fld.type)
                c += (f'<tr class="memitem:{fhash}" id="r_{fhash}">'
                      f'<td class="memItemLeft">{thtml}&#160;</td>'
                      f'<td class="memItemRight"><a class="el" '
                      f'href="#{fhash}">{esc(fld.name)}</a></td></tr>\n')
        elif entity.kind == 'enum' and entity.enum_values:
            c += ('<tr class="heading"><td colspan="2">'
                  '<h2 id="header-enum-members" class="groupheader">'
                  '<a id="enum-members" name="enum-members"></a>枚举值'
                  '</h2></td></tr>')
            for v in entity.enum_values:
                vhash = self._entity_hash(entity.name + '::' + v.name)
                vval = f" = {v.value}" if v.value else ""
                c += (f'<tr class="memitem:{vhash}" id="r_{vhash}">'
                      f'<td class="memItemLeft">{esc(v.name)}</td>'
                      f'<td class="memItemRight">{vval}</td></tr>\n')
        c += '</table>'

        c += ('<a name="details" id="details"></a>'
              '<h2 class="groupheader">详细描述</h2>'
              '<div class="textblock">')
        if entity.doc.details or entity.doc.brief:
            c += '<p>' + esc(entity.doc.details or entity.doc.brief) + '</p>'
        c += '</div>'

        # Member detail sections
        if entity.kind == 'struct' and entity.struct_fields:
            c += ('<a name="doc-variable-members" '
                  'id="doc-variable-members"></a>'
                  '<h2 class="groupheader">结构体成员变量说明</h2>')
            for fld in entity.struct_fields:
                fhash = self._entity_hash(entity.name + '::' + fld.name)
                thtml = self._type_link(fld.type)
                c += (f'<a id="{fhash}" name="{fhash}"></a>'
                      f'<h2 class="memtitle"><span class="permalink">'
                      f'<a href="#{fhash}">&#9670;&#160;</a></span>'
                      f'{esc(fld.name)}</h2>'
                      f'<div class="memitem"><div class="memproto">'
                      f'      <table class="memname"><tr>'
                      f'        <td class="memname">{thtml} '
                      f'{esc(entity.name)}::{esc(fld.name)}</td>'
                      f'      </tr></table>'
                      f'</div><div class="memdoc">')
                if fld.doc:
                    c += '<p>' + esc(fld.doc) + '</p>'
                c += '</div></div>'
        elif entity.kind == 'enum' and entity.enum_values:
            c += ('<a name="doc-enum-members" id="doc-enum-members"></a>'
                  '<h2 class="groupheader">枚举值说明</h2>')
            for v in entity.enum_values:
                vhash = self._entity_hash(entity.name + '::' + v.name)
                vval = f" = {v.value}" if v.value else ""
                c += (f'<a id="{vhash}" name="{vhash}"></a>'
                      f'<h2 class="memtitle"><span class="permalink">'
                      f'<a href="#{vhash}">&#9670;&#160;</a></span>'
                      f'{esc(v.name)}</h2>'
                      f'<div class="memitem"><div class="memproto">'
                      f'<table class="memname"><tr><td class="memname">'
                      f'{esc(entity.name)}::{esc(v.name)}{vval}'
                      f'</td></tr></table>'
                      f'</div><div class="memdoc"></div></div>')

        if inc_name:
            kind_cn = {'struct': '结构体', 'enum': '枚举', 'class': '类'}.get(
                entity.kind, entity.kind)
            c += (f'<hr/>该{kind_cn}的文档由以下文件生成:<ul>'
                  f'<li><a class="el" href="{inc_name}">'
                  f'{esc(fname)}</a></li></ul>')
        c += '</div>' + page_footer()
        path.write_text(c, encoding='utf-8')

    # ── Table renderers ──

    def _enum_table(self, entities):
        rows = ""
        for e in entities:
            brief = e.doc.brief or ""
            vals = []
            for v in e.enum_values:
                vtxt = v.name
                if v.value:
                    vtxt += f" = {v.value}"
                vals.append(vtxt)
            vals_str = ", ".join(vals[:8])
            if len(e.enum_values) > 8:
                vals_str += ", ..."
            anchor = "e_" + e.name
            inner = esc(e.name)
            if vals_str:
                inner += " { " + esc(vals_str) + " }"
            rows += (f'<tr class="memitem:{anchor}" id="r_{anchor}">'
                     f'<td class="memItemLeft">enum &#160;</td>'
                     f'<td class="memItemRight">'
                     f'<a class="el" href="#r_{anchor}">{inner}</a>'
                     f'</td></tr>\n')
            if brief:
                rows += (f'<tr class="memdesc:{anchor}">'
                         f'<td class="mdescLeft">&#160;</td>'
                         f'<td class="mdescRight">{esc(brief)}'
                         f'<br/></td></tr>\n')
        return (f'<table class="memberdecls">\n'
                f'{section_header("枚举", "enum-members")}{rows}</table>\n')

    def _struct_table(self, entities):
        rows = ""
        for e in entities:
            brief = e.doc.brief or ""
            page = self._entity_page_name(e)
            rows += (f'<tr class="memitem:s_{e.name}" id="r_s_{e.name}">'
                     f'<td class="memItemLeft">struct &#160;</td>'
                     f'<td class="memItemRight">'
                     f'<a class="el" href="{page}">{esc(e.name)}</a>'
                     f'</td></tr>\n')
            if brief:
                rows += (f'<tr class="memdesc:s_{e.name}">'
                         f'<td class="mdescLeft">&#160;</td>'
                         f'<td class="mdescRight">{esc(brief)}'
                         f'<br/></td></tr>\n')
        return (f'<table class="memberdecls">\n'
                f'{section_header("结构体", "struct-members")}'
                f'{rows}</table>\n')

    def _function_table(self, entities):
        rows = ""
        for e in entities:
            brief = e.doc.brief or ""
            parts = []
            for p in e.func_params:
                type_html = self._type_link(p.type.rstrip())
                parts.append(type_html + ' ' + p.name)
            sig = ', '.join(parts) if parts else ''
            rows += (f'<tr class="memitem:f_{e.name}" id="r_f_{e.name}">'
                     f'<td class="memItemLeft">{esc(e.func_return)}&#160;</td>'
                     f'<td class="memItemRight">'
                     f'<a class="el" href="#r_f_{e.name}">{esc(e.name)}</a>'
                     f'({sig})</td></tr>\n')
            if brief:
                rows += (f'<tr class="memdesc:f_{e.name}">'
                         f'<td class="mdescLeft">&#160;</td>'
                         f'<td class="mdescRight">{esc(brief)}'
                         f'<br/></td></tr>\n')
        return (f'<table class="memberdecls">\n'
                f'{section_header("函数", "func-members")}{rows}</table>\n')

    def _typedef_table(self, entities):
        rows = ""
        for e in entities:
            rows += (f'<tr class="memitem:t_{e.name}" id="r_t_{e.name}">'
                     f'<td class="memItemLeft">typedef &#160;</td>'
                     f'<td class="memItemRight">'
                     f'<a class="el" href="#">{esc(e.name)}</a>'
                     f'</td></tr>\n')
        return (f'<table class="memberdecls">\n'
                f'{section_header("类型定义", "typedef-members")}'
                f'{rows}</table>\n')

    def _simple_table(self, entities, kind):
        label = '宏定义' if kind == 'define' else '变量'
        anchor = 'define-members' if kind == 'define' else 'var-members'
        rows = ''
        for e in entities:
            pfx = kind[0]
            display = esc(e.name)
            if kind == 'define' and e.func_return:
                val_short = e.func_return.split('\n')[0][:60]
                display += ' = ' + esc(val_short)
            rows += (f'<tr class="memitem:{pfx}_{e.name}">'
                     f'<td class="memItemLeft">{label}&#160;</td>'
                     f'<td class="memItemRight">{display}</td></tr>\n')
        return (f'<table class="memberdecls">\n'
                f'{section_header(label, anchor)}{rows}</table>\n')

    # ── Globals pages ──

    def _write_globals_page(self):
        """Generate all globals category pages."""
        cats = {'all': [], 'function': [], 'vars': [], 'typedef': [],
                'enum': [], 'eval': [], 'defs': []}
        for fpath, finfo in self.files.items():
            for e in finfo.entities:
                letter = (e.name[0].upper()
                          if e.name and e.name[0].isalpha() else '_')
                cats['all'].append((letter, e, fpath))
                if e.kind == 'function':
                    cats['function'].append((letter, e, fpath))
                if e.kind == 'typedef':
                    cats['typedef'].append((letter, e, fpath))
                if e.kind == 'enum':
                    cats['enum'].append((letter, e, fpath))
                    for v in e.enum_values:
                        vl = (v.name[0].upper()
                              if v.name and v.name[0].isalpha() else '_')
                        cats['eval'].append((vl, None, fpath, v, e.name))
                if e.kind in ('struct', 'class'):
                    cats['typedef'].append((letter, e, fpath))
                if e.kind == 'define':
                    cats['defs'].append((letter, e, fpath))
                if e.kind == 'variable':
                    cats['vars'].append((letter, e, fpath))

        cat_config = [
            ('globals.html', '全部', 'all'),
            ('globals_func.html', '函数', 'function'),
            ('globals_type.html', '类型定义', 'typedef'),
            ('globals_enum.html', '枚举', 'enum'),
            ('globals_eval.html', '枚举值', 'eval'),
            ('globals_defs.html', '宏定义', 'defs'),
            ('globals_vars.html', '变量', 'vars'),
        ]

        def navrow3_tabs(active_key):
            tabs = ''
            for pname, label, key in cat_config:
                cls = ' class="current"' if key == active_key else ''
                tabs += f'<li{cls}><a href="{pname}"><span>{label}</span></a></li>\n'
            return f'<div id="navrow3" class="tabs2"><ul class="tablist">{tabs}</ul></div>'

        for page_name, title, key in cat_config:
            items = cats[key]
            if key == 'eval':
                by_letter = defaultdict(list)
                for item in items:
                    by_letter[item[0]].append(item)
            else:
                by_letter = defaultdict(list)
                for letter, e, fpath in items:
                    by_letter[letter].append((e, fpath))

            letters = sorted(by_letter.keys(), key=lambda x: (x == '_', x))
            c = page_doctype() + page_head(title)
            c += page_titlebar() + nav_tabs("files") + navrow3_tabs(key)
            letter_links = ''.join(
                f'<li><a href="#index_{l.lower()}"><span>{l}</span></a></li>'
                for l in letters)
            c += (f'<div id="navrow4" class="tabs3">'
                  f'<ul class="tablist">{letter_links}</ul></div>'
                  f'<div id="doc-content"><div class="header">'
                  f'<div class="headertitle"><div class="title">'
                  f'{title}</div></div></div><div class="contents">')

            if key == 'eval':
                for letter in letters:
                    c += (f'<h3 class="doxsection">'
                          f'<a id="index_{letter.lower()}" '
                          f'name="index_{letter.lower()}"></a>'
                          f'- {letter} -</h3><ul>')
                    for item in by_letter[letter]:
                        _letter, _, fpath, enum_val, enum_name = item
                        src = self._file_page_name(fpath)
                        ehash = self._entity_hash(
                            enum_name + '::' + enum_val.name)
                        c += (f'<li>{esc(enum_val.name)}&#160;:&#160;'
                              f'<a class="el" href="{src}#{ehash}">'
                              f'{esc(Path(fpath).name)}</a></li>\n')
                    c += '</ul>'
            else:
                for letter in letters:
                    c += (f'<h3 class="doxsection">'
                          f'<a id="index_{letter.lower()}" '
                          f'name="index_{letter.lower()}"></a>'
                          f'- {letter} -</h3><ul>')
                    for e, fpath in by_letter[letter]:
                        src = self._file_page_name(fpath)
                        fname = Path(fpath).name
                        if e.kind in ('struct', 'class', 'enum'):
                            page = self._entity_page_name(e)
                            c += (f'<li><a class="el" href="{page}">'
                                  f'{esc(e.name)}</a>&#160;:&#160;'
                                  f'<a class="el" href="{src}">'
                                  f'{esc(fname)}</a></li>\n')
                        else:
                            anchor = 'r_' + e.kind[0] + '_' + e.name
                            c += (f'<li><a class="el" href="{src}#{anchor}">'
                                  f'{esc(e.name)}</a>&#160;:&#160;'
                                  f'<a class="el" href="{src}">'
                                  f'{esc(fname)}</a></li>\n')
                    c += '</ul>'
            c += '</div>' + page_footer()
            (self.out / page_name).write_text(c, encoding='utf-8')

    # ── Main render entry ──

    def render_all(self):
        self.render_index_page()
        self.render_files_page()
        self.render_dir_pages()
        self.render_classes_page()
        self.render_class_index_page()
        self.render_pages_page()
        self._write_globals_page()
        for fpath in self.files:
            self.render_file_page(fpath)
            self.render_source_page(fpath)
        # Entity detail pages
        seen = set()
        for finfo in self.files.values():
            for e in finfo.entities:
                if e.kind in ('struct', 'class', 'enum') and e.name not in seen:
                    seen.add(e.name)
                    self.render_entity_page(e, finfo)


# ════════════════════════════════════════════════════════════════
# CHM Generator
# ════════════════════════════════════════════════════════════════

class ChmGenerator:
    """Generate CHM project files and compile via hhc.exe."""

    def __init__(self, files_dict, html_dir, chm_path):
        self.files = files_dict
        self.html_dir = Path(html_dir)
        self.chm_path = Path(chm_path)

    def _hhp_path(self):
        return self.html_dir / "project.hhp"

    def generate_hhp(self):
        c = ("[OPTIONS]\nCompatibility=1.1 or later\n"
             f"Compiled file={self.chm_path.resolve()}\n"
             "Contents file=project.hhc\nIndex file=project.hhk\n"
             "Default topic=index.html\n"
             "Title=iSulad Documentation\n"
             "Language=0x804 Chinese (PRC)\n"
             "Display compile progress=Yes\n"
             "Full-text search=Yes\nAuto Index=Yes\n\n[FILES]\n")
        seen = set()
        for glob_pat in ("*.html", "*.css", "*.js"):
            for f in sorted(self.html_dir.glob(glob_pat)):
                if f.name not in seen:
                    c += f.name + "\n"
                    seen.add(f.name)
        c += "\n[INFOTYPES]\n"
        with open(self._hhp_path(), "w", encoding="utf-8") as f:
            f.write(c)

    def generate_hhc(self):
        lines = [
            '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">',
            '<HTML><HEAD></HEAD><BODY>',
            '<OBJECT type="text/site properties">'
            '<param name="Window Styles" value="0x800025"></OBJECT>',
            '<UL>',
            '<LI><OBJECT type="text/sitemap">'
            '<param name="Name" value="首页">'
            '<param name="Local" value="index.html"></OBJECT>',
            '<LI><OBJECT type="text/sitemap">'
            '<param name="Name" value="结构体">'
            '<param name="Local" value="annotated.html"></OBJECT>',
            '<LI><OBJECT type="text/sitemap">'
            '<param name="Name" value="全局定义">'
            '<param name="Local" value="globals.html"></OBJECT>',
            '<LI><OBJECT type="text/sitemap">'
            '<param name="Name" value="文件">'
            '<param name="Local" value="files.html"></OBJECT>',
        ]
        # Build tree
        root = {}
        for fpath in sorted(self.files.keys()):
            fp = Path(fpath)
            try:
                parts = fp.parts
                idx = parts.index("iSulad")
                dir_parts = list(parts[idx:-1])
            except ValueError:
                dir_parts = list(fp.parts[:-1])
            node = root
            for d in dir_parts:
                node = node.setdefault(d, {})
            node["__files__"] = node.get("__files__", []) + [fp]

        def emit(node, indent=""):
            for key in sorted(node.keys()):
                if key == "__files__":
                    continue
                sub = node[key]
                has_kids = bool(sub) or bool(sub.get("__files__"))
                if not has_kids:
                    continue
                lines.append(f'{indent}<LI><OBJECT type="text/sitemap">')
                lines.append(f'{indent}  <param name="Name" value="{key}">')
                lines.append(f'{indent}</OBJECT>')
                lines.append(f'{indent}<UL>')
                for sk in sorted(sub.keys()):
                    if sk == "__files__":
                        continue
                    emit({sk: sub[sk]}, indent + "  ")
                for fp in sorted(sub.get("__files__", []),
                                 key=lambda x: x.name):
                    page = file_id(fp) + ".html"
                    lines.append(f'{indent}  <LI><OBJECT type="text/sitemap">')
                    lines.append(f'{indent}    <param name="Name" '
                                 f'value="{fp.name}">')
                    lines.append(f'{indent}    <param name="Local" '
                                 f'value="{page}">')
                    lines.append(f'{indent}  </OBJECT>')
                lines.append(f'{indent}</UL>')

        emit(root, "  ")
        lines.append('</UL></BODY></HTML>')
        with open(self.html_dir / "project.hhc", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def generate_hhk(self):
        with open(self.html_dir / "project.hhk", "w", encoding="utf-8") as f:
            f.write('<HTML><HEAD></HEAD><BODY></BODY></HTML>')

    def compile(self):
        self.generate_hhp()
        self.generate_hhc()
        self.generate_hhk()
        try:
            r = subprocess.run(
                [HHC, str(self._hhp_path())],
                capture_output=True, text=True, timeout=120)
            if r.returncode <= 1:
                if self.chm_path.exists():
                    print(f"  ✅ CHM: {self.chm_path.resolve()} "
                          f"({self.chm_path.stat().st_size:,} bytes)")
            else:
                print(f"  ❌ hhc.exe failed (rc={r.returncode})")
        except FileNotFoundError:
            print(f"  ❌ hhc.exe not found: {HHC}")
        except subprocess.TimeoutExpired:
            print("  ❌ hhc.exe timed out")


# ════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print(f"  {PROJECT_NAME} — Documentation Generator")
    print("=" * 60)

    parser = CParser()
    src_root = Path(__file__).resolve().parent
    for sd in SOURCE_DIRS:
        full = src_root / sd
        if full.is_dir():
            for f in sorted(full.rglob("*.h")):
                print(f"  📄 Parsing: {f}")
                parser.parse_file(f)
            for f in sorted(full.rglob("*.hpp")):
                print(f"  📄 Parsing: {f}")
                parser.parse_file(f)

    total = sum(len(f.entities) for f in parser.files.values())
    print(f"\n  📊 Parsed: {len(parser.files)} files, {total} entities")

    print("\n  🎨 Generating HTML pages...")
    html_dir = src_root / OUT_DIR
    html_dir.mkdir(parents=True, exist_ok=True)

    ref_dir = src_root / DOXYGEN_REF
    if ref_dir.is_dir():
        for asset in ["doxygen.css", "tabs.css", "navtree.css",
                       "jquery.js", "dynsections.js", "doxygen.svg"]:
            src = ref_dir / asset
            if src.exists():
                shutil.copy2(src, html_dir / asset)
                print(f"  📋 Copied: {asset}")
    else:
        print(f"  ⚠ Reference dir not found: {ref_dir}")

    hgen = HtmlGenerator(parser.files, html_dir)
    hgen.render_all()
    html_count = len(list(html_dir.glob("*.html")))
    print(f"  ✅ {html_count} HTML pages generated in {html_dir}")

    print("\n  📚 Generating CHM...")
    chm_path = src_root / CHM_FILE
    chm = ChmGenerator(parser.files, html_dir, chm_path)
    chm.compile()

    print("\n" + "=" * 60)
    print("  Done.")
    print(f"  HTML:  {html_dir.resolve()}")
    print(f"  CHM:   {chm_path.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
