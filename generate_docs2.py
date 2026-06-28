#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_docs.py — C/C++ header doc generator matching Doxygen 1.16.1 output.
Parses /** comments from .h/.hpp files in iSulad/src and generates HTML
pages matching the 123123/html Doxygen reference style.
"""

import re, sys, html as html_mod, shutil
from pathlib import Path

# ────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────
PROJECT_NAME    = "iSulad"
PROJECT_NUMBER  = ""
PROJECT_BRIEF   = "iSulad - Lightweight container runtime"
OUT_DIR         = Path("docs") / "html"
DOXYGEN_REF     = Path("..") / "123123" / "html"
SOURCE_DIRS     = [Path("..") / "iSulad" / "src"]
PAGE_EXT        = ".html"
ENCODING        = "utf-8"

# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────
def E(text):
    return html_mod.escape(text or "")

def safe_name(text):
    """sanitize → safe filename"""
    return re.sub(r'[^a-zA-Z0-9_]', '_', (text or "")).lower()[:64]

def file_id(filepath):
    """Convert path like .../common/constants.h → constants_8h
       Doxygen convention: underscores in filenames become __ in page names.
       e.g. adaptor_cri.h → adaptor__cri_8h.html, constants.h → constants_8h.html
    """
    name = filepath.name
    base = name.rsplit('.',1)[0] if '.' in name else name
    ext  = name.rsplit('.',1)[1] if '.' in name else ""
    # Doxygen doubles underscores in filenames
    safe_base = base.replace('_', '__')
    return f"{safe_base}_8{ext}"

def dir_id(dirpath):
    """hash-like directory id (mimics Doxygen dir_xxxxx)"""
    import hashlib
    h = hashlib.md5(str(dirpath).encode()).hexdigest()[:12]
    return f"dir_{h}"

class DocComment:
    def __init__(self, raw=""):
        self.brief = ""
        self.details = ""
        self.params = []       # (direction, name, desc)
        self.return_ = ""
        self.retvals = []      # [(code, desc)]
        self.pre = ""
        self.post = ""
        self.note = ""
        self.warning = ""
        self.see = ""
        self.deprecated = ""
        self._parse(raw)

    def _parse(self, raw):
        if not raw or not raw.strip(): return
        text = raw.strip()
        # Strip leading *
        text = re.sub(r'^\s*\*\s?', '', text, flags=re.MULTILINE)
        self.brief = self._extract(r'@brief\s+(.*?)(?:\s*@|\s*$)', text) or ""
        self.details = self._extract(r'@details\s+(.*?)(?:\s*@|\s*$)', text) or ""
        self.return_ = self._extract(r'@return\s+(.*?)(?:\s*@|\s*$)', text) or ""
        self.pre = self._extract(r'@pre\s+(.*?)(?:\s*@|\s*$)', text) or ""
        self.post = self._extract(r'@post\s+(.*?)(?:\s*@|\s*$)', text) or ""
        self.note = self._extract(r'@note\s+(.*?)(?:\s*@|\s*$)', text) or ""
        self.warning = self._extract(r'@warning\s+(.*?)(?:\s*@|\s*$)', text) or ""
        self.see = self._extract(r'@see\s+(.*?)(?:\s*@|\s*$)', text) or ""
        self.deprecated = self._extract(r'@deprecated\s+(.*?)(?:\s*@|\s*$)', text) or ""
        # params
        for m in re.finditer(r'@param\s*\[?(\w*)\]?\s+(\w[\w_]*)\s+(.*?)(?=\s*@|\s*$)', text, re.DOTALL):
            d = m.group(1) or "in"
            n = m.group(2)
            desc = m.group(3).strip()
            self.params.append((d, n, desc))
        # retvals
        for m in re.finditer(r'@retval\s+(\S+)\s+(.*?)(?=\s*@|\s*$)', text, re.DOTALL):
            self.retvals.append((m.group(1), m.group(2).strip()))
        if not self.brief:
            # First sentence as brief
            first = re.split(r'[.]\s', text, maxsplit=1)
            if first: self.brief = first[0].strip()
        if not self.details and not self.brief:
            self.details = text

    def _extract(self, pat, text):
        m = re.search(pat, text, re.DOTALL)
        return m.group(1).strip() if m else ""

    def has_content(self):
        return any([self.brief, self.details])

    @property
    def return_(self):
        return self._return

    @return_.setter
    def return_(self, v):
        self._return = v

# ────────────────────────────────────────────────────────────────────
# C Header Parser
# ────────────────────────────────────────────────────────────────────
class ParseError(Exception):
    pass

class DocEntity:
    TYPES = {"enum":1,"struct":2,"function":3,"define":4,"typedef":5}
    def __init__(self, kind, name, doc=None):
        self.kind = kind
        self.name = name
        self.doc = doc or DocComment()
        self.raw_decl = ""
        self.enum_values = []
        self.struct_fields = []
        self.func_params = []
        self.func_return = ""

class FileInfo:
    """Holds all entities found in one .h file."""
    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.entities = []  # list of DocEntity

class CParser:
    def __init__(self):
        self.files = {}  # str(filepath) → FileInfo
        self._doc_accum = []
        self._pending_doc = None
        self._in_doc_block = False
        self._in_skip_block = False
        self._trailing_doc = ""
        self._accum_block = False
        self._current_file = None

    def _add_entity(self, kind, name, decl_line):
        src = self._pending_doc if (not self._doc_accum and self._pending_doc) else self._doc_accum
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

    def _finalize_enum(self, match, line):
        name = match.group(2) if match.lastindex >= 2 else ""
        e = self._add_entity("enum", name, line.strip())
        body = match.group(1) if match.lastindex >= 1 else ""
        # Split body by comma (respecting brace depth)
        parts = []; cur = ""; depth = 0
        for ch in body:
            if ch in '{(': depth += 1; cur += ch
            elif ch in '})': depth -= 1; cur += ch
            elif ch == ',' and depth == 0: parts.append(cur.strip()); cur = ""
            else: cur += ch
        if cur.strip(): parts.append(cur.strip())
        from collections import namedtuple
        EnumValue = namedtuple("EnumValue", "name value doc")
        for p in parts:
            vm = re.match(r'(\w[\w_]*)\s*(=\s*[^,]+?)?\s*(?:\/\*\*\s*<\s*(.*?)\s*\*\/)?\s*$', p.strip(), re.DOTALL)
            if vm:
                vn = vm.group(1)
                vv = (vm.group(2) or "").strip().lstrip('= ')
                vd = vm.group(3).strip() if vm.lastindex >= 3 and vm.group(3) else ""
                e.enum_values.append(EnumValue(vn, vv, vd))
        return e

    def _finalize_struct(self, match, line):
        name = match.group(2) if match.lastindex >= 2 else ""
        e = self._add_entity("struct", name, line.strip())
        body = match.group(1) if match.lastindex >= 1 else ""
        # Simple field parsing by splitting on ;
        from collections import namedtuple
        Field = namedtuple("Field", "type name doc")
        for part in body.split(';'):
            p = part.strip()
            if not p or p.startswith('#') or p.startswith('//') or p.startswith('/*'): continue
            doc = ""
            dm = re.search(r'/\*\*\s*<\s*(.*?)\s*\*/', p, re.DOTALL)
            if dm: doc = dm.group(1).strip(); p = p[:dm.start()].strip()
            p = re.sub(r'//.*', '', p).strip()
            # Skip struct/union member function declarations and nested types
            if '(' in p and ')' in p: continue
            if p.startswith('struct ') or p.startswith('union '): continue
            words = p.split()
            if len(words) >= 2:
                fname = words[-1].rstrip(';').strip('[]')
                ftype = ' '.join(words[:-1])
                e.struct_fields.append(Field(ftype, fname, doc))
        return e

    def _parse_func(self, decl_line):
        decl = decl_line.strip().rstrip(';').strip()
        # Strip trailing /**< doc
        m = re.search(r'/\*\*\s*<\s*(.*?)\s*\*/', decl, re.DOTALL)
        trailing_doc = ""
        if m: trailing_doc = m.group(1).strip(); decl = decl[:m.start()].strip()
        m = re.match(r'((?:\w[\w\s\*]*?))[\s\*]+(\w[\w_]*)\s*\(([^)]*)\)', decl)
        if not m: return None
        ret = m.group(1).strip()
        fname = m.group(2).strip()
        params_str = m.group(3) if m.lastindex >= 3 else ""
        e = self._add_entity("function", fname, decl_line.strip())
        e.func_return = ret
        if trailing_doc: e.doc = DocComment(trailing_doc)
        if params_str.strip() and params_str != "void":
            from collections import namedtuple
            Param = namedtuple("Param", "type name direction doc")
            for p in params_str.split(','):
                p = p.strip()
                if not p: continue
                pm = re.match(r'(?:(\w+)\s+)?([\w_\*]+)\s+(\*?\w[\w_]*)\s*$', p)
                if pm:
                    prefix = pm.group(1) or ""
                    ptype = pm.group(2)
                    pname = pm.group(3)
                    if prefix in ("const","struct","unsigned","signed","static"):
                        ptype = f"{prefix} {ptype}"
                    pdoc = ""
                    direction = "in"
                    for (d, dn, desc) in e.doc.params:
                        if dn == pname: pdoc = desc; direction = d; break
                    e.func_params.append(Param(ptype, pname, direction, pdoc))
        return e

    def _process_doc_directives(self):
        text = "\n".join(self._doc_accum)
        if text.strip() and not any(kw in text for kw in ['@addtogroup','@defgroup','@}','@{','@file']):
            self._pending_doc = self._doc_accum.copy()
        self._doc_accum = []

    def feed_line(self, lineno, line):
        stripped = line.strip()
        # Skip /***... (copyright banners), only treat /** (exactly 2 asterisks) as Doxygen
        if re.match(r'^/\*{3,}', stripped):
            if "*/" in stripped: return
            self._in_skip_block = True; return
        if getattr(self, '_in_skip_block', False):
            if "*/" in stripped: self._in_skip_block = False
            return
        tm = re.search(r'/\*\*<\s*(.*?)\s*\*/', stripped)
        if tm: self._trailing_doc = tm.group(1)
        # Doc block handling
        # Doxygen doc: must be /**x (not /*** banner)
        if re.match(r'^/\*\*(?:[^*]|$)', stripped) and "*/" in stripped and not stripped.startswith("/**<"):
            content = re.sub(r'^/\*\*\s*', '', stripped); content = re.sub(r'\s*\*/$', '', content)
            self._doc_accum.append(content); self._in_doc_block = False
            self._process_doc_directives(); return
        if re.match(r'^/\*\*(?:[^*]|$)', stripped) and not stripped.startswith("/**<"):
            self._doc_accum = []
            content = re.sub(r'^/\*\*\s*', '', stripped)
            if content and "*/" in content:
                content = content.replace("*/","").strip()
                self._doc_accum.append(content); self._in_doc_block = False
                self._process_doc_directives(); return
            if content: self._doc_accum.append(content)
            self._in_doc_block = True; return
        if self._in_doc_block:
            if "*/" in stripped:
                content = re.sub(r'\s*\*/$','',stripped); content = re.sub(r'^\s*\*\s?','',content)
                if content: self._doc_accum.append(content)
                self._in_doc_block = False; self._process_doc_directives(); return
            else:
                content = re.sub(r'^\s*\*\s?','',stripped)
                if content: self._doc_accum.append(content)
                return
        # Multi-line typedef accumulation
        if getattr(self, '_accum_block', False):
            self._accum_block[0].append(line)
            for ch in line:
                if ch == '{': self._accum_block[1] += 1
                elif ch == '}': self._accum_block[1] -= 1
            if self._accum_block[1] == 0:
                full = '\n'.join(self._accum_block[0]); self._accum_block = False
                em = re.match(r'typedef\s+enum\s*\{(.*)\}\s*(\w[\w_]*)\s*;', full, re.DOTALL)
                if em: self._finalize_enum(em, line); return
                sm = re.match(r'typedef\s+struct\s*\{(.*)\}\s*(\w[\w_]*)\s*;', full, re.DOTALL)
                if sm: self._finalize_struct(sm, line); return
                # C++ style: enum Name { ... };
                em2 = re.match(r'enum\s+(\w[\w_]*)\s*\{(.*)\}', full, re.DOTALL)
                if em2:
                    e = self._add_entity("enum", em2.group(1), line.strip())
                    parts = [p.strip() for p in em2.group(2).replace('\n','').split(',') if p.strip()]
                    from collections import namedtuple
                    EV = namedtuple("EnumValue", "name value doc")
                    for p in parts:
                        vm = re.match(r'(\w[\w_]*)\s*(=\s*[^,]+)?', p.strip())
                        if vm:
                            e.enum_values.append(EV(vm.group(1), (vm.group(2) or '').lstrip('= '), ''))
                    return
                # C++ style: struct Name { ... };
                sm2 = re.match(r'struct\s+(\w[\w_]*)\s*\{(.*)\}', full, re.DOTALL)
                if sm2:
                    e = self._add_entity("struct", sm2.group(1), line.strip())
                    from collections import namedtuple
                    Field = namedtuple("Field", "type name doc")
                    for part in sm2.group(2).split(';'):
                        p = part.strip()
                        if not p or p.startswith('#') or p.startswith('//'): continue
                        p = re.sub(r'//.*', '', p).strip()
                        words = p.split()
                        if len(words) >= 2:
                            e.struct_fields.append(Field(' '.join(words[:-1]), words[-1].rstrip(';]'), ''))
                    return
            return
        # Start accumulation for enum/struct (simple brace blocks)
        for kw in [r'typedef\s+(enum|struct)\s*\{',
                   r'enum\s+\w+\s*\{',
                   r'struct\s+\w+\s*\{']:
            if re.match(kw, stripped) and '};' not in stripped and not stripped.endswith(';'):
                self._accum_block = [[line], 0]
                for ch in line:
                    if ch == '{': self._accum_block[1] += 1
                    elif ch == '}': self._accum_block[1] -= 1
                return
        # class: just declare, don't accumulate (body has nested methods with {})
        cm = re.match(r'class\s+(\w[\w_]*)', stripped)
        if cm and stripped.endswith('{'):
            self._add_entity('class', cm.group(1), line.strip())
            self._doc_accum = []
            return
        # Single-line typedefs
        m = re.match(r'typedef\s+enum\s*\{(.*?)\}\s*(\w[\w_]*)\s*;', stripped, re.DOTALL)
        if m: self._finalize_enum(m, line); return
        m = re.match(r'typedef\s+struct\s*\{(.*?)\}\s*(\w[\w_]*)\s*;', stripped, re.DOTALL)
        if m: self._finalize_struct(m, line); return
        m = re.match(r'typedef\s+(?!enum\s*\{)(?!struct\s*\{)(.+?)\s+(\w[\w_]*)\s*;', stripped)
        if m:
            self._add_entity("typedef", m.group(2), line.strip())
            self._doc_accum = []; return
        # Function detection
        func_skip = {"typedef","if","for","while","return","switch","case","#define","#include","#if","#ifdef","#ifndef","#else","#endif"}
        first_word = stripped.split()[0] if stripped.split() else ""
        if (stripped and not stripped.startswith("#") and first_word not in func_skip
            and not stripped.startswith("//") and not stripped.startswith("/*")
            and "(" in stripped and ")" in stripped
            and not stripped.startswith("extern") and not stripped.startswith("struct ")):
            e = self._parse_func(line)
            if e: return
        if stripped == "" or stripped.startswith("//") or stripped.startswith("/*"): pass
        elif not self._in_doc_block: self._doc_accum = []

    def parse_file(self, filepath):
        self.filepath = str(filepath)
        self._current_file = FileInfo(filepath)
        self._doc_accum = []
        self._pending_doc = None
        self._in_doc_block = False
        self._in_skip_block = False
        self._trailing_doc = ""
        self._accum_block = False
        try:
            with open(filepath, encoding='utf-8', errors='replace') as f:
                for i, line in enumerate(f, 1):
                    self.feed_line(i, line)
        except Exception as e:
            print(f"  ⚠ Error parsing {filepath}: {e}")
        self.files[str(filepath)] = self._current_file


# ────────────────────────────────────────────────────────────────────
# HTML Page templates
# ────────────────────────────────────────────────────────────────────

def page_doctype():
    return '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "https://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'

def page_head(title):
    return f'''<html xmlns="http://www.w3.org/1999/xhtml" lang="en-US">
<head>
<meta http-equiv="Content-Type" content="text/xhtml;charset=UTF-8"/>
<meta http-equiv="X-UA-Compatible" content="IE=11"/>
<meta name="generator" content="Doc Generator 1.0"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{PROJECT_NAME}: {E(title)}</title>
<link href="doxygen.css" rel="stylesheet" type="text/css" />
<link href="tabs.css" rel="stylesheet" type="text/css" />
</head><body>
'''

def page_titlebar():
    num = f'<span id="projectnumber">&#160;{E(PROJECT_NUMBER)}</span>' if PROJECT_NUMBER else ''
    brief = f'<div id="projectbrief">{E(PROJECT_BRIEF)}</div>' if PROJECT_BRIEF else ''
    return f'''<div id="top">
<div id="titlearea">
<table cellspacing="0" cellpadding="0">
 <tbody>
 <tr id="projectrow">
  <td id="projectalign">
   <div id="projectname">{E(PROJECT_NAME)}{num}</div>
   {brief}
  </td>
 </tr>
 </tbody>
</table>
</div>
'''

def page_subtabs(active_section="files"):
    def li(page, label, href):
        cls = ' class="current"' if page == active_section else ''
        return f'<li{cls}><a href="{href}"><span>{label}</span></a></li>'
    if active_section in ("classes", "classindex"):
        cur_cls = "classes" if active_section == "classes" else "classindex"
        return f'''  <div id="navrow2" class="tabs2">
    <ul class="tablist">
{li("classes","Structs","annotated.html")}
{li("classindex","Class Index","classes.html")}
    </ul>
  </div>
'''
    return f'''  <div id="navrow2" class="tabs2">
    <ul class="tablist">
{li("files","File List","files.html")}
{li("globals","Globals","globals.html")}
    </ul>
  </div>
'''

def nav_tabs(active_page="main"):
    def li(page, label):
        cls = ' class="current"' if page == active_page else ''
        href = {"main":"index.html","topics":"modules.html","classes":"annotated.html",
                "files":"files.html","pages":"pages.html"}.get(page, "index.html")
        return f'<li{cls}><a href="{href}"><span>{label}</span></a></li>'
    return f'''<div id="main-nav">
  <div id="navrow1" class="tabs">
    <ul class="tablist">
{li("main","Main&#160;Page")}
{li("pages","Related&#160;Pages")}
{li("classes","Classes")}
{li("files","Files")}
    </ul>
  </div>
</div>
</div><!-- top -->
'''

def _highlight_code(escaped_text):
    """Apply syntax highlighting spans to HTML-escaped source code."""
    line = escaped_text
    
    # Comments (// to end of line)
    line = re.sub(r'(\/\/.*$)', r'<span class="comment">\1</span>', line, flags=re.MULTILINE)
    # Comments (/* ... */)
    line = re.sub(r'(\/\*.*?\*\/)', r'<span class="comment">\1</span>', line, flags=re.DOTALL)
    
    # Preprocessor directives at start of line  
    line = re.sub(r'^(#\s*(?:include|define|ifdef|ifndef|endif|else|elif|pragma|error|warning)\b.*)',
                  r'<span class="preprocessor">\1</span>', line, flags=re.MULTILINE)
    
    # String literals (in HTML-escaped text, quotes are &quot;)
    line = re.sub(r'(&quot;(?:[^&]|&(?!quot;))*?&quot;)', r'<span class="stringliteral">\1</span>', line)
    
    # C++ keywords (must be simple ASCII words, not inside tags)
    keywords = r'\b(alignas|alignof|auto|bool|break|case|catch|class|const|constexpr|continue|decltype|default|delete|do|double|else|enum|explicit|export|extern|false|final|float|for|friend|goto|if|inline|int|long|mutable|namespace|new|noexcept|nullptr|operator|override|private|protected|public|register|return|short|signed|sizeof|static|static_cast|struct|switch|template|this|throw|true|try|typedef|typeid|typename|union|unsigned|using|virtual|void|volatile|while)\b'
    # Split by existing tags and highlight keywords outside them
    parts = re.split(r'(<span[^>]*>|</span>)', line)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(keywords, r'<span class="keyword">\1</span>', parts[i])
    line = ''.join(parts)
    
    return line

def page_footer():
    return '''<hr class="footer"/><address class="footer"><small>
Generated by&#160;<b>Doc Generator</b>
</small></address>
</div><!-- doc-content -->
</body></html>'''

def section_header(title, anchor_id):
    return f'''<tr class="heading"><td colspan="2"><h2 id="header-{anchor_id}" class="groupheader"><a id="{anchor_id}" name="{anchor_id}"></a>
{title}</h2></td></tr>'''


# ────────────────────────────────────────────────────────────────────
# HTML Generator
# ────────────────────────────────────────────────────────────────────

class HtmlGenerator:
    def __init__(self, parsed_files, out_dir):
        self.files = parsed_files  # dict path → FileInfo
        self.out = Path(out_dir)
        self.out.mkdir(parents=True, exist_ok=True)

    def _file_page_name(self, filepath):
        return file_id(Path(filepath)) + PAGE_EXT

    # ── Index page ──
    def render_index_page(self):
        path = self.out / "index.html"
        c = page_doctype() + page_head(PROJECT_NAME)
        c += page_titlebar() + nav_tabs("main")
        c += f'''<div id="doc-content">
<div class="header"><div class="headertitle"><div class="title">{E(PROJECT_NAME)} </div></div></div>
<div class="contents">
<div class="textblock"><p>{E(PROJECT_BRIEF)}</p>
<h1>Overview</h1>
<p>iSulad is a lightweight container runtime.</p>
<h1>Modules</h1>
<p>The source code is organized under the following directories:</p>
<ul>
<li><code>api/</code> - API definitions</li>
<li><code>client/</code> - Client library</li>
<li><code>cmd/</code> - Command line tools</li>
<li><code>common/</code> - Common utilities</li>
<li><code>daemon/</code> - Daemon implementation</li>
<li><code>utils/</code> - Utility functions</li>
</ul>
</div></div>''' + page_footer()
        path.write_text(c, encoding='utf-8')

    # ── File list page ──
    def _dir_id(self, dir_path):
        import hashlib
        h = hashlib.md5(str(dir_path).lower().encode()).hexdigest()[:32]
        return f"dir_{h}"

    def _build_dir_tree(self):
        root = {"name": "iSulad", "path": "iSulad", "subdirs": {}, "files": [], "id": self._dir_id("iSulad")}
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
                dp = "/".join(parts[start:i+1])
                if p not in node["subdirs"]:
                    node["subdirs"][p] = {"name": p, "path": dp, "subdirs": {}, "files": [], "id": self._dir_id(dp), "parent": node}
                node = node["subdirs"][p]
            node["files"].append(fp)
        return root

    def _render_tree_rows(self, node, depth=0, row=0, pid=""):
        h = ""
        rid = f"{pid}{row}_"
        indent = depth * 16
        oe = "even" if row % 2 == 0 else "odd"
        has_kids = bool(node["subdirs"] or node["files"])
        arrow = f'<span id="arr_{rid}" class="arrow" onclick="dynsection.toggleFolder(\'{rid}\')"><span class="arrowhead opened"></span></span>' if has_kids else '<span style="width:16px;display:inline-block;">&#160;</span>'
        icon = f'<span id="img_{rid}" class="iconfolder" onclick="dynsection.toggleFolder(\'{rid}\')"><div class="folder-icon open"></div></span>'
        h += f'<tr id="row_{rid}" class="{oe}"><td class="entry"><span style="width:{indent}px;display:inline-block;">&#160;</span>{arrow}{icon}<a class="el" href="{node["id"]}{PAGE_EXT}" target="_self">{E(node["name"])}</a></td><td class="desc"></td></tr>\n'
        ci = 0
        for sd in sorted(node["subdirs"].values(), key=lambda x: x["name"]):
            h += self._render_tree_rows(sd, depth+1, ci, rid)
            ci += 1
        for f in sorted(node["files"]):
            fid = file_id(f)
            fbrief = ""
            fs = str(f)
            if fs in self.files and self.files[fs].entities:
                fbrief = self.files[fs].entities[0].doc.brief or ""
            cid = f"{rid}{ci}"
            coe = "even" if ci % 2 == 0 else "odd"
            ci += 1
            h += f'<tr id="row_{cid}" class="{coe}"><td class="entry"><span style="width:{(depth+1)*16}px;display:inline-block;">&#160;</span><span style="width:16px;display:inline-block;">&#160;</span><span class="icon"><div class="file-icon"></div></span><a class="el" href="{fid}{PAGE_EXT}">{E(f.name)}</a></td><td class="desc">{E(fbrief[:120]) if fbrief else ""}</td></tr>\n'
        return h

    def render_files_page(self):
        root = self._build_dir_tree()
        c = page_doctype() + page_head("File List")
        c += page_titlebar() + nav_tabs("files")
        c += '''<div id="doc-content">
<div class="header"><div class="headertitle"><div class="title">File List</div></div></div>
<div class="contents">
<div class="textblock">Here is a list of all documented header files:</div>
<div class="directory">
<div class="levels">[detail levels <span onclick="javascript:dynsection.toggleLevel(1);">1</span><span onclick="javascript:dynsection.toggleLevel(2);">2</span><span onclick="javascript:dynsection.toggleLevel(3);">3</span><span onclick="javascript:dynsection.toggleLevel(4);">4</span><span onclick="javascript:dynsection.toggleLevel(5);">5</span><span onclick="javascript:dynsection.toggleLevel(6);">6</span><span onclick="javascript:dynsection.toggleLevel(7);">7</span><span onclick="javascript:dynsection.toggleLevel(8);">8</span><span onclick="javascript:dynsection.toggleLevel(9);">9</span><span onclick="javascript:dynsection.toggleLevel(10);">10</span>]</div>
<table class="directory">
'''
        c += self._render_tree_rows(root)
        c += '''</table>
</div>
</div>''' + page_footer()
        self.out.joinpath("files.html").write_text(c, encoding='utf-8')

    def render_dir_pages(self):
        def walk(node):
            did = node["id"]
            parts = node["path"].replace("\\", "/").split("/")
            title = "/".join(parts[-3:]) if len(parts) >= 3 else node["name"]
            c = page_doctype() + page_head(f"{title} Directory Reference")
            c += page_titlebar() + nav_tabs("files")
            c += '<div id="nav-path" class="navpath"><ul>'
            for i in range(len(parts)):
                dp = "/".join(parts[:i+1])
                c += f'<li class="navelem"><a href="{self._dir_id(dp)}{PAGE_EXT}">{E(parts[i])}</a></li>'
            c += '</ul></div></div><!-- top -->'
            c += f'<div id="doc-content"><div class="header"><div class="headertitle"><div class="title">{E(node["name"])} Directory Reference</div></div></div><div class="contents">\n'
            if node["subdirs"]:
                c += '<table class="memberdecls"><tr class="heading"><td colspan="2"><h2 id="header-subdirs" class="groupheader"><a id="subdirs" name="subdirs"></a>Directories</h2></td></tr>\n'
                for sd in sorted(node["subdirs"].values(), key=lambda x: x["name"]):
                    c += f'<tr class="memitem:{sd["name"]}"><td class="memItemLeft"><span class="iconfolder"><div class="folder-icon"></div></span>&#160;</td><td class="memItemRight"><a class="el" href="{sd["id"]}{PAGE_EXT}">{E(sd["name"])}</a></td></tr>\n'
                c += '</table>\n'
            if node["files"]:
                c += '<table class="memberdecls"><tr class="heading"><td colspan="2"><h2 id="header-files" class="groupheader">Files</h2></td></tr>\n'
                for f in sorted(node["files"]):
                    fid = file_id(f)
                    fb = ""
                    fs = str(f)
                    if fs in self.files and self.files[fs].entities:
                        fb = self.files[fs].entities[0].doc.brief or ""
                    c += f'<tr class="memitem:{fid}"><td class="memItemLeft">file &#160;</td><td class="memItemRight"><a class="el" href="{fid}{PAGE_EXT}">{E(f.name)}</a></td></tr>\n'
                    if fb:
                        c += f'<tr class="memdesc:{fid}"><td class="mdescLeft">&#160;</td><td class="mdescRight">{E(fb[:120])}<br/></td></tr>\n'
                c += '</table>\n'
            c += '</div>' + page_footer()
            (self.out / f"{did}{PAGE_EXT}").write_text(c, encoding='utf-8')
            for sd in node["subdirs"].values():
                walk(sd)
        walk(self._build_dir_tree())

    # ── File documentation page ──
    def _real_includes(self, fpath):
        """Extract #include lines with delimiter info."""
        includes = []
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    m = re.match(r'\s*#\s*include\s+([<"])(.+?)[>"]', line)
                    if m:
                        delim = m.group(1)  # < or "
                        name = m.group(2)
                        includes.append((delim, name))
        except:
            pass
        return includes[:20]

    def render_file_page(self, fpath):
        finfo = self.files[fpath]
        fp = Path(fpath)
        page_name = self._file_page_name(fpath)
        path = self.out / page_name
        src_name = page_name.replace('.html', '_source.html')

        # Relative path and breadcrumbs
        try:
            idx = str(fpath).index("iSulad\\src\\")
            rel_path = str(fpath)[idx + len("iSulad\\src\\"):].replace('\\', '/')
            dir_parts = ["iSulad", "src"] + rel_path.rsplit('/', 1)[0].split('/')
        except ValueError:
            rel_path = fp.name
            dir_parts = [fp.name]

        # Breadcrumb dir IDs
        dir_ids = []
        for i in range(1, len(dir_parts) + 1):
            dp = "/".join(dir_parts[:i])
            dir_ids.append((dir_parts[i-1], self._dir_id(dp)))

        c = page_doctype()
        c += page_head(fp.name)
        c += page_titlebar()
        c += nav_tabs("files")
        # Second nav row
        c += page_subtabs("files")
        # Breadcrumbs
        c += '<div id="nav-path" class="navpath"><ul>'
        for name, did in dir_ids:
            c += f'<li class="navelem"><a href="{did}{PAGE_EXT}">{E(name)}</a></li>'
        c += '<li class="navelem"><a class="el" href="#">' + E(fp.name) + '</a></li>'
        c += '</ul></div></div><!-- top -->'

        c += '<div id="doc-content">\n'

        # Header with summary
        by_kind = {}
        for e in finfo.entities:
            by_kind.setdefault(e.kind, []).append(e)
        summary_links = []
        kind_labels = {"struct":"Classes","enum":"Enumerations","function":"Functions","typedef":"Typedefs"}
        for kind in ["struct","enum","function","typedef"]:
            if kind in by_kind:
                anchor = {"struct":"struct-members","enum":"enum-members","function":"func-members","typedef":"typedef-members"}[kind]
                summary_links.append(f'<a href="#{anchor}">{kind_labels[kind]}</a>')
        summary_bar = ' | '.join(summary_links) + '\n  ' if summary_links else ''

        c += f'''<div class="header">
  <div class="summary">
{summary_bar}</div>
  <div class="headertitle"><div class="title">{E(fp.name)}</div></div>
</div><!--header-->
<div class="contents">
'''
        # Real #include directives from source (matching Doxygen format)
        raw_includes = self._real_includes(fpath)
        if raw_includes:
            c += '<div class="textblock">'
            for delim, inc in raw_includes:
                # Try to match against documented files
                linked = False
                inc_norm = inc.replace('/', '\\')
                for fkey in self.files:
                    if fkey.endswith(inc) or fkey.endswith(inc_norm):
                        src_name = self._file_page_name(fkey).replace(PAGE_EXT, '_source' + PAGE_EXT)
                        open_d = '&lt;' if delim == '<' else '&quot;'
                        close_d = '&gt;' if delim == '<' else '&quot;'
                        c += f'<code>#include {open_d}<a class="el" href="{src_name}">{E(inc)}</a>{close_d}</code><br />\n'
                        linked = True
                        break
                if not linked:
                    open_d = '&lt;' if delim == '<' else '&quot;'
                    close_d = '&gt;' if delim == '<' else '&quot;'
                    c += f'<code>#include {open_d}{E(inc)}{close_d}</code><br />\n'
            c += '</div>\n'
        # Source file link
        c += f'<p><a href="{src_name}">Go to the source code of this file.</a></p>\n'

        # Member declaration tables
        for kind in ["struct","enum","function","typedef"]:
            if kind in by_kind:
                if kind == "struct":
                    c += self._struct_table(by_kind[kind])
                elif kind == "enum":
                    c += self._enum_table(by_kind[kind])
                elif kind == "function":
                    c += self._function_table(by_kind[kind])
                elif kind == "typedef":
                    c += self._typedef_table(by_kind[kind])

        # Detailed descriptions
        has_detail = False
        for e in finfo.entities:
            if e.doc.details or e.doc.brief:
                if not has_detail:
                    c += '<a name="details" id="details"></a>\n'
                    has_detail = True
                c += f'''<h2 class="groupheader">{E(e.name)} {e.kind.title()}</h2>
<div class="textblock"><p>{E(e.doc.details or e.doc.brief)}</p></div>
'''

        # Function full documentation
        for e in by_kind.get("function", []):
            c += f'<a name="doc-func-members" id="doc-func-members"></a>\n'
            anchor = "r_f_" + e.name
            c += f'<a id="{anchor}" name="{anchor}"></a>\n'
            c += f'<h2 class="memtitle"><span class="permalink"><a href="#{anchor}">&#9670;&#160;</a></span>{e.name}()</h2>\n'
            c += '<div class="memitem">\n<div class="memproto">\n'
            c += '      <table class="memname">\n        <tr>\n'
            c += f'          <td class="memname">{E(e.func_return)} {E(e.name)} </td>\n'
            c += '          <td>(</td>\n'
            for i, p in enumerate(e.func_params):
                c += f'          <td class="paramtype">{E(p.type)}</td>\n'
                c += f'          <td class="paramname"><em>{E(p.name)}</em></td>\n'
                if i < len(e.func_params) - 1:
                    c += '          <td>,</td>\n'
            if not e.func_params:
                c += '          <td class="paramname">void</td>\n'
            c += '          <td>)</td>\n        </tr>\n      </table>\n'
            c += '</div><div class="memdoc">\n'
            if e.doc.brief:
                c += f"<p>{E(e.doc.brief)}</p>\n"
            if e.func_params:
                c += '<dl class="params"><dt>Parameters</dt><dd>\n  <table class="params">\n'
                for p in e.func_params:
                    c += f'    <tr><td class="paramname">{E(p.name)}</td><td>{E(p.doc)}</td></tr>\n'
                c += '  </table>\n</dd></dl>\n'
            if e.doc.return_:
                c += f'<dl class="section return"><dt>Returns</dt><dd>{E(e.doc.return_)}</dd></dl>\n'
            if e.doc.retvals:
                c += '<dl class="retval"><dt>Return values</dt><dd>\n  <table class="retval">\n'
                for code, desc in e.doc.retvals:
                    c += f'    <tr><td class="paramname">{E(code)}</td><td>{E(desc)}</td></tr>\n'
                c += '  </table>\n</dd></dl>\n'
            c += '</div></div>\n'

        c += page_footer()
        path.write_text(c, encoding='utf-8')


    
    def render_source_page(self, fpath):
        """Generate source code view page matching Doxygen 1.16.1 format."""
        fp = Path(fpath)
        pname = self._file_page_name(fpath).replace(PAGE_EXT, "_source" + PAGE_EXT)
        doc_page = self._file_page_name(str(fpath))
        out_path = self.out / pname
        try:
            s = str(fpath).replace('\\', '/')
            idx = s.index("iSulad/src/")
            rel = s[idx:]
            dir_parts = rel.split('/')[:-1]
        except:
            dir_parts = ["iSulad"]
        c = page_doctype()
        c += page_head(fp.name + " source")
        c += page_titlebar() + nav_tabs("files") + page_subtabs("files")
        c += '<div id="nav-path" class="navpath"><ul>'
        for i in range(1, len(dir_parts) + 1):
            dp = "/".join(dir_parts[:i])
            c += f'<li class="navelem"><a href="{self._dir_id(dp)}{PAGE_EXT}">{E(dir_parts[i-1])}</a></li>'
        c += '</ul></div></div><!-- top -->'
        c += '<div id="doc-content"><div class="header"><div class="headertitle"><div class="title">' + E(fp.name) + '</div></div></div>'
        c += '<div class="contents">'
        c += f'<a href="{doc_page}">Go to the documentation of this file.</a>'
        c += '<div class="fragment">'
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as sf:
                for i, l in enumerate(sf.readlines()):
                    anchor = f"l{i+1:05d}"
                    visible = f"{i+1:5d}"
                    escaped = html_mod.escape(l.rstrip('\n\r'))
                    highlighted = _highlight_code(escaped)
                    c += f'<div class="line"><a id="{anchor}" name="{anchor}"></a><span class="lineno"> {visible}</span> {highlighted}</div>\n'
        except Exception as ex:
            c += f'<p>Error: {ex}</p>'
        c += '</div></div>' + page_footer()
        out_path.write_text(c, encoding="utf-8")

    def _enum_table(self, entities):
        rows = ""
        for e in entities:
            brief = e.doc.brief or ""
            anchor = "enum_" + e.name
            # Build inline enum values string (matching Doxygen format)
            vals = []
            for v in e.enum_values:
                vtxt = v.name
                if v.value:
                    vtxt += f" = {v.value}"
                vals.append(vtxt)
            vals_str = ", ".join(vals[:8])
            if len(e.enum_values) > 8:
                vals_str += ", ..."
            if vals_str:
                rows += f'<tr class="memitem:e_{e.name}" id="r_e_{e.name}"><td class="memItemLeft">enum &#160;</td><td class="memItemRight"><a class="el" href="#">{E(e.name)}</a> &#123; {E(vals_str)} &#125;</td></tr>\n'
            else:
                rows += f'<tr class="memitem:e_{e.name}" id="r_e_{e.name}"><td class="memItemLeft">enum &#160;</td><td class="memItemRight"><a class="el" href="#">{E(e.name)}</a></td></tr>\n'
            if brief:
                rows += f'<tr class="memdesc:{e.name}"><td class="mdescLeft">&#160;</td><td class="mdescRight">{E(brief)}<br/></td></tr>\n'
        return f'<table class="memberdecls">\n{section_header("Enumerations", "enum-members")}{rows}</table>\n'

    def _struct_table(self, entities):
        rows = ""
        for e in entities:
            brief = e.doc.brief or ""
            rows += f'<tr class="memitem:s_{e.name}" id="r_s_{e.name}"><td class="memItemLeft">struct &#160;</td><td class="memItemRight"><a class="el" href="{self._entity_page_name(e)}">{E(e.name)}</a></td></tr>\n'
            if brief:
                rows += f'<tr class="memdesc:s_{e.name}"><td class="mdescLeft">&#160;</td><td class="mdescRight">{E(brief)}<br/></td></tr>\n'
        return f'<table class="memberdecls">\n{section_header("Structures", "struct-members")}{rows}</table>\n'

    def _function_table(self, entities):
        rows = ""
        for e in entities:
            brief = e.doc.brief or ""
            rows += f'<tr class="memitem:f_{e.name}" id="r_f_{e.name}"><td class="memItemLeft">{E(e.func_return)}&#160;</td><td class="memItemRight"><a class="el" href="#r_f_{e.name}">{E(e.name)}</a>({E(", ".join(p.type for p in e.func_params))})</td></tr>\n'
            if brief:
                rows += f'<tr class="memdesc:f_{e.name}"><td class="mdescLeft">&#160;</td><td class="mdescRight">{E(brief)}<br/></td></tr>\n'
        return f'<table class="memberdecls">\n{section_header("Functions", "func-members")}{rows}</table>\n'

    def _typedef_table(self, entities):
        rows = ""
        for e in entities:
            rows += f'<tr class="memitem:t_{e.name}" id="r_t_{e.name}"><td class="memItemLeft">typedef &#160;</td><td class="memItemRight"><a class="el" href="#r_t_{e.name}">{E(e.name)}</a></td></tr>\n'
        return f'<table class="memberdecls">\n{section_header("Typedefs", "typedef-members")}{rows}</table>\n'

    
    def _entity_page(self, type_name):
        """If type_name matches a known entity, return the page URL."""
        for finfo in self.files.values():
            for e in finfo.entities:
                if e.name == type_name:
                    return self._entity_page_name(e)
        return None

    def _type_link(self, type_name):
        """Generate <a> link for a type reference to its entity page."""
        page = self._entity_page(type_name)
        if page:
            return f'<a class="el" href="{page}">{E(type_name)}</a>'
        return E(type_name)

    def render_entity_page(self, entity, finfo):
        """Generate a standalone entity detail page matching Doxygen 1.16.1 format."""
        pname = self._entity_page_name(entity)
        path = self.out / pname
        fpath = getattr(finfo, 'path', None)
        fname = fpath.name if fpath else entity.name
        inc_name = file_id(fpath) + PAGE_EXT if fpath else ""
        src_page = inc_name.replace(PAGE_EXT, "_source" + PAGE_EXT) if inc_name else ""

        c = page_doctype()
        c += page_head(f"{entity.name} {entity.kind.title()} Reference")
        c += page_titlebar() + nav_tabs("classes") + page_subtabs("classes")

        # Breadcrumb
        c += '<div id="nav-path" class="navpath"><ul>'
        c += f'<li class="navelem"><a class="el" href="{pname}">{E(entity.name)}</a></li>'
        c += '</ul></div></div><!-- top -->'

        c += '<div id="doc-content"><div class="header">'
        summary = '<a href="#pub-attribs">Members</a>' if (entity.kind == 'struct' and entity.struct_fields) or entity.enum_values else ''
        c += f'  <div class="summary">{summary}</div>'
        c += '  <div class="headertitle"><div class="title">' + E(entity.name) + ' ' + entity.kind.title() + ' Reference</div></div>'
        c += '</div><!--header--><div class="contents">'

        # Include with source link
        if inc_name:
            c += f'<p><code>#include &lt;<a class="el" href="{inc_name}">{E(fname)}</a>&gt;</code></p>'

        # Member table
        c += '<table class="memberdecls">'
        if entity.kind == 'struct' and entity.struct_fields:
            c += '<tr class="heading"><td colspan="2"><h2 id="header-pub-attribs" class="groupheader"><a id="pub-attribs" name="pub-attribs"></a>Members</h2></td></tr>'
            for fld in entity.struct_fields:
                fhash = self._entity_hash(entity.name + '::' + fld.name)
                thtml = self._type_link(fld.type)
                c += f'<tr class="memitem:{fhash}" id="r_{fhash}"><td class="memItemLeft">{thtml}&#160;</td><td class="memItemRight"><a class="el" href="#{fhash}">{E(fld.name)}</a></td></tr>\n'
        elif entity.kind == 'enum' and entity.enum_values:
            c += '<tr class="heading"><td colspan="2"><h2 id="header-enum-members" class="groupheader"><a id="enum-members" name="enum-members"></a>Enum Values</h2></td></tr>'
            for v in entity.enum_values:
                vhash = self._entity_hash(entity.name + '::' + v.name)
                vval = f" = {v.value}" if v.value else ""
                c += f'<tr class="memitem:{vhash}" id="r_{vhash}"><td class="memItemLeft">{E(v.name)}</td><td class="memItemRight">{vval}</td></tr>\n'
        c += '</table>'

        # Details
        c += '<a name="details" id="details"></a><h2 class="groupheader">Detailed Description</h2>'
        c += '<div class="textblock">'
        if entity.doc.details or entity.doc.brief:
            c += '<p>' + E(entity.doc.details or entity.doc.brief) + '</p>'
        c += '</div>'

        # Member detail sections
        if entity.kind == 'struct' and entity.struct_fields:
            c += '<a name="doc-variable-members" id="doc-variable-members"></a>'
            c += '<h2 class="groupheader">Member Data Documentation</h2>'
            for fld in entity.struct_fields:
                fhash = self._entity_hash(entity.name + '::' + fld.name)
                thtml = self._type_link(fld.type)
                c += f'<a id="{fhash}" name="{fhash}"></a>'
                c += f'<h2 class="memtitle"><span class="permalink"><a href="#{fhash}">&#9670;&#160;</a></span>{E(fld.name)}</h2>'
                c += '<div class="memitem"><div class="memproto">'
                c += '      <table class="memname"><tr>'
                c += f'        <td class="memname">{thtml} {E(entity.name)}::{E(fld.name)}</td>'
                c += '      </tr></table>'
                c += '</div><div class="memdoc">'
                if fld.doc:
                    c += '<p>' + E(fld.doc) + '</p>'
                c += '</div></div>'
        elif entity.kind == 'enum' and entity.enum_values:
            c += '<a name="doc-enum-members" id="doc-enum-members"></a>'
            c += '<h2 class="groupheader">Enum Value Documentation</h2>'
            for v in entity.enum_values:
                vhash = self._entity_hash(entity.name + '::' + v.name)
                vval = f" = {v.value}" if v.value else ""
                c += f'<a id="{vhash}" name="{vhash}"></a>'
                c += f'<h2 class="memtitle"><span class="permalink"><a href="#{vhash}">&#9670;&#160;</a></span>{E(v.name)}</h2>'
                c += '<div class="memitem"><div class="memproto">'
                c += f'      <table class="memname"><tr><td class="memname">{E(entity.name)}::{E(v.name)}{vval}</td></tr></table>'
                c += '</div><div class="memdoc"></div></div>'

        # Footer file list
        if inc_name:
            c += '<hr/>The documentation for this ' + entity.kind + ' was generated from:<ul>'
            c += f'<li><a class="el" href="{inc_name}">{E(fname)}</a></li></ul>'
        c += '</div>' + page_footer()
        path.write_text(c, encoding='utf-8')

    def render_class_index_page(self):
        path = self.out / "classes.html"
        c = page_doctype() + page_head("Class Index")
        c += page_titlebar() + nav_tabs("classes") + page_subtabs("classindex")
        c += '<div id="doc-content"><div class="header"><div class="headertitle"><div class="title">Class Index</div></div></div><div class="contents"><div class="textblock"><p>See the <a href="annotated.html">Class List</a> for all documented structures.</p></div></div>' + page_footer()
        path.write_text(c, encoding='utf-8')

    def render_classes_page(self):
        path = self.out / "annotated.html"
        c = page_doctype() + page_head("Class List")
        c += page_titlebar() + nav_tabs("classes")
        c += '''<div id="doc-content">
<div class="header"><div class="headertitle"><div class="title">Class List</div></div></div>
<div class="contents">
<div class="textblock"><p>Class documentation is available in the file-level pages.</p></div>''' + page_footer()
        path.write_text(c, encoding='utf-8')

    
    def _write_globals_page(self):
        """Generate placeholder globals.html."""
        c = page_doctype() + page_head("Globals")
        c += page_titlebar() + nav_tabs("files") + page_subtabs("globals")
        c += '<div id="doc-content"><div class="header"><div class="headertitle"><div class="title">Globals</div></div></div><div class="contents"><div class="textblock"><p>Global definitions are available in the file-level documentation.</p></div></div>' + page_footer()
        (self.out / "globals.html").write_text(c, encoding='utf-8')

    def render_pages_page(self):
        path = self.out / "pages.html"
        c = page_doctype() + page_head("Related Pages")
        c += page_titlebar() + nav_tabs("pages")
        c += '''<div id="doc-content">
<div class="header"><div class="headertitle"><div class="title">Related Pages</div></div></div>
<div class="contents">
<div class="textblock"><p><a href="index.html">Main Page</a></p></div>''' + page_footer()
        path.write_text(c, encoding='utf-8')

    def _entity_hash(self, name):
        import hashlib
        return 'a' + hashlib.md5(name.encode()).hexdigest()[:32]

    def _entity_page_name(self, entity, ns=''):
        prefix = entity.kind
        qname = (ns + '::' + entity.name) if ns else entity.name
        safe = qname.replace('::', '_1_1')
        return f'{prefix}_{safe}{PAGE_EXT}'

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
        for fpath in self.files:
            self.render_source_page(fpath)
        # Generate entity detail pages for structs, classes, and enums
        seen = set()
        for finfo in self.files.values():
            for e in finfo.entities:
                if e.kind in ('struct', 'class', 'enum') and e.name not in seen:
                    seen.add(e.name)
                    self.render_entity_page(e, finfo)


# ────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────

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

    print(f"\n  📊 Parsed: {len(parser.files)} files, {sum(len(f.entities) for f in parser.files.values())} entities")

    print("\n  🎨 Generating HTML pages...")
    html_dir = src_root / OUT_DIR
    html_dir.mkdir(parents=True, exist_ok=True)

    # Copy Doxygen assets
    ref_dir = src_root / DOXYGEN_REF
    if ref_dir.is_dir():
        for asset in ["doxygen.css","tabs.css","navtree.css","jquery.js","dynsections.js","doxygen.svg"]:
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

    print("\n" + "=" * 60)
    print("  Done.")
    print(f"  HTML:  {html_dir.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
