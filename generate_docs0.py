#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_docs.py — C header doc generator matching Doxygen 1.16.1 output.
Parses /** comments, @addtogroup / @{ / @} groups, enums, structs, and
functions from .h files, then generates HTML that mirrors Doxygen's
exact styling and layout, plus compiles CHM via hhc.exe.
"""

import re, sys, html as html_mod
from pathlib import Path

# ────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────
PROJECT_NAME    = "Sensor Data Acquisition Library"
PROJECT_NUMBER  = "1.0.0"
PROJECT_BRIEF   = "Embedded sensor driver & signal-processing library"
OUT_DIR         = Path("docs") / "html"
CHM_FILE        = Path("..") / "sensor_library.chm"
HHC             = r"C:\Program Files (x86)\HTML Help Workshop\hhc.exe"
SOURCE_DIRS     = [Path("include"), Path("src")]
PAGE_EXT        = ".html"
ENCODING        = "utf-8"

# ────────────────────────────────────────────────────────────────────
# Data classes
# ────────────────────────────────────────────────────────────────────

class DocComment:
    def __init__(self, raw=""):
        self.brief = ""
        self.details = ""
        self.params = []       # (direction, name, desc)
        self.return_ = ""
        self.retvals = []      # (code, desc)
        self.pre = ""
        self.post = ""
        self.note = ""
        self.warning = ""
        self.see = ""
        self.raw = raw
        if raw:
            self._parse(raw)

    def _parse(self, text):
        def get_tag(tag, t=text):
            m = re.search(r'@' + tag + r'\s+(.*?)(?=\s*@\w|\s*$)', t, re.DOTALL)
            return m.group(1).strip() if m else ""
        self.brief = get_tag("brief")
        self.details = get_tag("details")
        self.return_ = get_tag("return") or get_tag("returns")
        self.pre = get_tag("pre")
        self.post = get_tag("post")
        self.note = get_tag("note")
        self.warning = get_tag("warning")
        self.see = get_tag("see")
        # params
        for m in re.finditer(r'@param\s*(?:\[(\w+)\])?\s+(\w[\w_]*)\s+(.*?)(?=\s*@\w|\s*$)', text, re.DOTALL):
            d = m.group(1) if m.group(1) else "in"
            self.params.append((d, m.group(2), m.group(3).strip()))
        # retvals
        for m in re.finditer(r'@retval\s+(\S+)\s+(.*?)(?=\s*@\w|\s*$)', text, re.DOTALL):
            self.retvals.append((m.group(1), m.group(2).strip()))

    def has_content(self):
        return bool(self.brief or self.details or self.params or self.return_ or
                    self.retvals or self.pre or self.post or self.note or
                    self.warning or self.see)


class EnumValue:
    def __init__(self, name, value="", doc=""):
        self.name = name; self.value = value; self.doc = doc

class StructField:
    def __init__(self, type_str, name, doc=""):
        self.type = type_str; self.name = name; self.doc = doc

class FuncParam:
    def __init__(self, type_str, name, direction="in", doc=""):
        self.type = type_str; self.name = name
        self.direction = direction; self.doc = doc

class DocEntity:
    TYPES = {"enum": 1, "struct": 2, "function": 3, "define": 4, "typedef": 5}
    def __init__(self, kind, name, doc=None):
        self.kind = kind
        self.name = name
        self.doc = doc or DocComment()
        self.raw_decl = ""
        self.enum_values = []
        self.struct_fields = []
        self.func_params = []
        self.func_return = ""
        self.anchor_id = None  # stable anchor like doxygen's gaXXXXXX

    def entity_id(self):
        """Stable, unique HTML anchor."""
        if self.anchor_id:
            return self.anchor_id
        clean = re.sub(r'[^a-zA-Z0-9_]', '_', f"{self.kind}_{self.name}").lower()
        return clean[:64]

    @property
    def anchor(self):
        return self.entity_id()


class DocGroup:
    def __init__(self, name, brief="", details=""):
        self.name = name
        self.brief = brief
        self.details = details
        self.parent = None
        self.subgroups = {}
        self.entities = []

    def flat_entities(self):
        yield from self.entities
        for sg in self.subgroups.values():
            yield from sg.flat_entities()


# ────────────────────────────────────────────────────────────────────
# C Parser
# ────────────────────────────────────────────────────────────────────

class CParser:
    def __init__(self):
        self.root = DocGroup("__root__")
        self.groups = {"__root__": self.root}
        self.stack = [self.root]
        self._doc_accum = []
        self._in_doc_block = False
        self._pending_doc = None
        self._in_skip_block = False
        self._trailing_doc = ""
        self._accum_typedef = False
        self._line_num = 0

    def _current_group(self):
        return self.stack[-1] if self.stack else self.root

    def _add_entity(self, kind, name, decl_line):
        # Use pending doc if doc_accum is empty and pending exists
        if not self._doc_accum and getattr(self, '_pending_doc', None):
            src = self._pending_doc
        else:
            src = self._doc_accum
        doc = DocComment("\n".join(src)) if src else DocComment()
        e = DocEntity(kind, name, doc)
        e.raw_decl = decl_line
        self._pending_doc = None
        if self._trailing_doc:
            if not doc.has_content():
                e.doc = DocComment(self._trailing_doc)
            self._trailing_doc = ""
        self._current_group().entities.append(e)
        self._doc_accum = []
        return e

    def _process_doc_directives(self):
        text = "\n".join(self._doc_accum)
        # Save non-group doc as pending for the next entity
        if text.strip() and not any(kw in text for kw in ['@addtogroup','@defgroup','@}','@{','@file']):
            self._pending_doc = self._doc_accum.copy()
        for line in text.split("\n"):
            ll = line.strip()
            if "@addtogroup" in ll:
                m = re.search(r'@addtogroup\s+(\w[\w_]*)', ll)
                if m:
                    gname = m.group(1)
                    brief = ""
                    details = ""
                    bm = re.search(r'@brief\s+(.+?)(?:\s*@|\s*$)', text, re.DOTALL)
                    if bm: brief = bm.group(1).strip()
                    dm = re.search(r'@details\s+(.+?)(?:\s*@|\s*$)', text, re.DOTALL)
                    if dm: details = dm.group(1).strip()
                    if not brief:
                        bm2 = re.search(r'@brief\s+(.+)', ll)
                        if bm2: brief = bm2.group(1).strip()
                    if gname not in self.groups:
                        g = DocGroup(gname, brief, details)
                        cur = self._current_group()
                        cur.subgroups[gname] = g
                        g.parent = cur
                        self.groups[gname] = g
                        self.stack.append(g)
            if "@defgroup" in ll:
                m = re.search(r'@defgroup\s+(\w[\w_]*)', ll)
                if m and m.group(1) not in self.groups:
                    gname = m.group(1)
                    brief = (re.search(r'@brief\s+(.+)', ll) or [None,""])[1] or ""
                    g = DocGroup(gname, brief.strip() if isinstance(brief,str) else "")
                    im = re.search(r'@ingroup\s+(\w[\w_]*)', ll)
                    if im:
                        p = self.groups.get(im.group(1))
                        if p: p.subgroups[gname] = g; g.parent = p
                        else: self.root.subgroups[gname] = g; g.parent = self.root
                    else:
                        self.root.subgroups[gname] = g; g.parent = self.root
                    self.groups[gname] = g
            if "@{" in ll and "@addtogroup" not in ll and "@defgroup" not in ll:
                pass
            if "@}" in ll and len(self.stack) > 1:
                self.stack.pop()
        self._doc_accum = []

    def _finalize_enum(self, match, line):
        name = match.group(2) if match.lastindex >= 2 else ""
        e = self._add_entity("enum", name, line.strip())
        body = match.group(1) or ""
        parts = []
        depth = 0; cur = ""
        for ch in body:
            if ch in '{(': depth += 1; cur += ch
            elif ch in '})': depth -= 1; cur += ch
            elif ch == ',' and depth == 0:
                if cur.strip(): parts.append(cur.strip())
                cur = ""
            else: cur += ch
        if cur.strip(): parts.append(cur.strip())
        for p in parts:
            m = re.match(r'(\w[\w_]*)\s*(=\s*[^,]+?)?\s*(?:\/\*\*\s*<?\s*(.*?)\s*\*\/)?\s*$', p, re.DOTALL)
            if m:
                vname = m.group(1)
                vval = (m.group(2) or "").replace("=","").strip()
                vdoc = m.group(3).strip() if m.lastindex >= 3 and m.group(3) else ""
                e.enum_values.append(EnumValue(vname, vval, vdoc))

    def _finalize_struct(self, match, line):
        name = match.group(2) if match.lastindex >= 2 else ""
        e = self._add_entity("struct", name, line.strip())
        body = match.group(1) or ""
        depth = 0; cur = ""
        for ch in body:
            if ch in '{(': depth += 1; cur += ch
            elif ch in '})': depth -= 1; cur += ch
            elif ch == ';' and depth == 0:
                self._parse_struct_field(cur.strip(), e); cur = ""
            else: cur += ch
        if cur.strip(): self._parse_struct_field(cur.strip(), e)

    def _parse_struct_field(self, decl, entity):
        if not decl: return
        doc = ""
        m = re.search(r'/\*\*\s*<?\s*(.*?)\s*\*/', decl, re.DOTALL)
        if m: doc = m.group(1).strip(); decl = decl[:m.start()].strip()
        decl = decl.rstrip(';').strip()
        decl = re.sub(r'//.*', '', decl).strip()
        parts = decl.split()
        if len(parts) >= 2:
            name = parts[-1].rstrip(';').strip()
            etype = ' '.join(parts[:-1])
            entity.struct_fields.append(StructField(etype, name, doc))

    def _parse_func(self, decl_line):
        decl = decl_line.strip().rstrip(';').strip()
        m = re.search(r'/\*\*\s*<?\s*(.*?)\s*\*/', decl, re.DOTALL)
        trailing_doc = ""
        if m: trailing_doc = m.group(1).strip(); decl = decl[:m.start()].strip()
        m = re.match(r'((?:\w[\w\s\*]*?))\s+(\w[\w_]*)\s*\(([^)]*)\)\s*$', decl)
        if not m: m = re.match(r'((?:\w[\w\s\*]*?))\s+(\w[\w_]*)\s*\(', decl)
        if m:
            ret = m.group(1).strip()
            fname = m.group(2).strip()
            params_str = m.group(3) if m.lastindex >= 3 else ""
            e = self._add_entity("function", fname, decl_line.strip())
            e.func_return = ret
            if trailing_doc: e.doc = DocComment(trailing_doc)
            if params_str.strip():
                for p in params_str.split(','):
                    p = p.strip()
                    if p and p != "void":
                        pm = re.match(r'(?:(\w+)\s+)?(\w[\w_\*]*)\s+(\w[\w_]*)\s*$', p)
                        if pm:
                            prefix = pm.group(1) or ""
                            ptype = pm.group(2)
                            pname = pm.group(3)
                            if prefix in ("const","struct","unsigned","signed","static"):
                                ptype = f"{prefix} {ptype}"
                            pdoc = ""
                            for (d, dn, dd) in e.doc.params:
                                if dn == pname: pdoc = dd; break
                            direction = "in"
                            for (d, dn, dd) in e.doc.params:
                                if dn == pname: direction = d; break
                            e.func_params.append(FuncParam(ptype, pname, direction, pdoc))
            return e
        return None

    def feed_line(self, lineno, line):
        stripped = line.strip()
        # Skip non-doxygen /* ... */
        if stripped.startswith("/*") and not stripped.startswith("/**"):
            if "*/" in stripped: return
            self._in_skip_block = True; return
        if getattr(self, '_in_skip_block', False):
            if "*/" in stripped: self._in_skip_block = False
            return
        # Trailing /**< ... */
        tm = re.search(r'/\*\*<\s*(.*?)\s*\*/', stripped)
        if tm: self._trailing_doc = tm.group(1)
        # Single-line /** ... */
        if stripped.startswith("/**") and "*/" in stripped and not stripped.startswith("/**<"):
            content = re.sub(r'^/\*\*\s*', '', stripped)
            content = re.sub(r'\s*\*/$', '', content)
            content = re.sub(r'^\*\s?', '', content)
            self._doc_accum.append(content)
            self._in_doc_block = False
            self._process_doc_directives()
            return
        # Multi-line /** start
        if stripped.startswith("/**") and not stripped.startswith("/**<"):
            self._doc_accum = []
            content = re.sub(r'^/\*\*\s*', '', stripped)
            if content:
                if "*/" in content:
                    content = content.replace("*/","").strip()
                    self._doc_accum.append(content)
                    self._in_doc_block = False
                    self._process_doc_directives()
                    return
                self._doc_accum.append(content)
            self._in_doc_block = True
            return
        # Doc continuation
        if self._in_doc_block:
            if "*/" in stripped:
                content = re.sub(r'\s*\*/$','',stripped)
                content = re.sub(r'^\s*\*\s?','',content)
                if content: self._doc_accum.append(content)
                self._in_doc_block = False
                self._process_doc_directives()
                return
            content = re.sub(r'^\s*\*\s?','',stripped)
            if content: self._doc_accum.append(content)
            return
        # ── Standalone directives ──
        if "@addtogroup" in stripped:
            m = re.search(r'@addtogroup\s+(\w[\w_]*)', stripped)
            if m:
                gname = m.group(1)
                doc_t = "\n".join(self._doc_accum)
                brief = ""
                bm = re.search(r'@brief\s+(.+?)(?:\s*@|\s*$)', doc_t + "\n" + stripped, re.DOTALL)
                if bm: brief = bm.group(1).strip()
                if not brief:
                    bm2 = re.search(r'@brief\s+(.+)', stripped)
                    if bm2: brief = bm2.group(1).strip()
                if gname not in self.groups:
                    g = DocGroup(gname, brief)
                    cur = self._current_group()
                    cur.subgroups[gname] = g; g.parent = cur
                    self.groups[gname] = g
                    self.stack.append(g)
                self._doc_accum = []; return
        if "@defgroup" in stripped:
            m = re.search(r'@defgroup\s+(\w[\w_]*)', stripped)
            if m and m.group(1) not in self.groups:
                gname = m.group(1)
                brief = (re.search(r'@brief\s+(.+)', stripped) or [None,""]).groups()[0] or ""
                g = DocGroup(gname, brief.strip())
                im = re.search(r'@ingroup\s+(\w[\w_]*)', stripped)
                if im:
                    p = self.groups.get(im.group(1))
                    if p: p.subgroups[gname] = g; g.parent = p
                    else: self.root.subgroups[gname] = g; g.parent = self.root
                else: self.root.subgroups[gname] = g; g.parent = self.root
                self.groups[gname] = g
                self.stack.append(g)
                self._doc_accum = []; return
        if "@{" in stripped:
            self._doc_accum = []; return
        if "@}" in stripped and len(self.stack) > 1:
            self.stack.pop(); self._doc_accum = []; return
        # ── Entity declarations ──
        if "@ingroup" in stripped:
            self._doc_accum.append(stripped); return
        # Multi-line typedef accum
        if getattr(self, '_accum_typedef', False):
            self._accum_typedef.append(line)
            if re.search(r'\}\s*\w*\s*;', line.strip()):
                full = '\n'.join(self._accum_typedef)
                self._accum_typedef = False
                em = re.match(r'typedef\s+enum\s*\{(.*?)\}\s*(\w[\w_]*)\s*;', full, re.DOTALL)
                if em: self._finalize_enum(em, line); return
                sm = re.match(r'typedef\s+struct\s*\{(.*?)\}\s*(\w[\w_]*)\s*;', full, re.DOTALL)
                if sm: self._finalize_struct(sm, line); return
            return
        if re.match(r'typedef\s+(enum|struct)\s*\{', stripped) and '};' not in stripped:
            self._accum_typedef = [line]; return
        # Single-line
        m = re.match(r'typedef\s+enum\s*\{(.*?)\}\s*(\w[\w_]*)\s*;', stripped, re.DOTALL)
        if m: self._finalize_enum(m, line); return
        m = re.match(r'typedef\s+struct\s*\{(.*?)\}\s*(\w[\w_]*)\s*;', stripped, re.DOTALL)
        if m: self._finalize_struct(m, line); return
        # Simple typedef
        m = re.match(r'typedef\s+(?!enum\s*\{)(?!struct\s*\{)(.+?)\s+(\w[\w_]*)\s*;', stripped)
        if m:
            if not m.group(1).strip().startswith("struct") and "(*" not in stripped:
                e = self._add_entity("typedef", m.group(2), line.strip())
                self._doc_accum = []; return
            elif m.group(1).strip().startswith("struct"):
                e = self._add_entity("typedef", m.group(2), line.strip())
                self._doc_accum = []; return
            elif "(*" in stripped:
                e = self._add_entity("typedef", m.group(2), line.strip())
                self._doc_accum = []; return
            self._doc_accum = []; return
        # Function
        func_skip = {"typedef","if","for","while","return","switch","case","#define","#include","#if","#ifdef","#ifndef","#else","#endif"}
        first_word = stripped.split()[0] if stripped.split() else ""
        if (stripped and not stripped.startswith("#") and first_word not in func_skip
            and not stripped.startswith("//") and not stripped.startswith("/*")
            and "(" in stripped and ")" in stripped
            and not stripped.startswith("extern")):
            e = self._parse_func(line)
            if e: return
        if not stripped or stripped.startswith("//") or stripped.startswith("/*"):
            pass
        elif not self._in_doc_block:
            self._doc_accum = []

    def parse_file(self, filepath):
        self.filepath = str(filepath)
        try:
            with open(filepath, encoding=ENCODING) as f:
                for i, line in enumerate(f, 1):
                    self.feed_line(i, line)
        except Exception as e:
            print(f"  ⚠ Error parsing {filepath}: {e}", file=sys.stderr)


# ────────────────────────────────────────────────────────────────────
# HTML Generation — matches Doxygen 1.16.1 layout exactly
# ────────────────────────────────────────────────────────────────────

E = html_mod.escape

def page_doctype():
    return '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "https://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'

def page_head(title):
    return f"""<html xmlns="http://www.w3.org/1999/xhtml" lang="en-US">
<head>
<meta http-equiv="Content-Type" content="text/xhtml;charset=UTF-8"/>
<meta http-equiv="X-UA-Compatible" content="IE=11"/>
<meta name="generator" content="Reasonix Doc Generator 1.0"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{E(PROJECT_NAME)}: {E(title)}</title>
<link href="doxygen.css" rel="stylesheet" type="text/css" />
<link href="tabs.css" rel="stylesheet" type="text/css" />
</head>"""

def page_titlebar():
    return f"""<body>
<div id="top"><!-- do not remove this div, it is closed by doxygen! -->
<div id="titlearea">
<table cellspacing="0" cellpadding="0">
 <tbody>
 <tr id="projectrow">
  <td id="projectalign">
   <div id="projectname">{E(PROJECT_NAME)}<span id="projectnumber">&#160;{E(PROJECT_NUMBER)}</span>
   </div>
   <div id="projectbrief">{E(PROJECT_BRIEF)}</div>
  </td>
 </tr>
 </tbody>
</table>
</div>
<!-- end header part -->"""

def nav_tabs(active_page="main"):
    """active_page: main | topics | classes | files | pages"""
    def li(page, label):
        cls = ' class="current"' if page == active_page else ''
        href = {"main":"index.html","topics":"modules.html","classes":"annotated.html",
                "files":"files.html","pages":"pages.html"}[page]
        return f'<li{cls}><a href="{href}"><span>{label}</span></a></li>'
    return f"""<div id="main-nav">
  <div id="navrow1" class="tabs">
    <ul class="tablist">
{li("main","Main&#160;Page")}
{li("pages","Related&#160;Pages")}
{li("topics","Topics")}
{li("classes","Classes")}
{li("files","Files")}
    </ul>
  </div>
</div><!-- main-nav -->
</div><!-- top -->"""

def page_footer():
    return """<hr class="footer"/><address class="footer"><small>
Generated by&#160;<b>Reasonix Doc Generator</b>
</small></address>
</div><!-- doc-content -->
</body>
</html>"""

def ingroups_breadcrumb(entity, group_lookup=None):
    """Build ingroups trail like: Sensor_api &raquo; Sensor_data"""
    parts = []
    g = getattr(entity, '_group', None)
    if g and g.name != "__root__":
        chain = []
        c = g
        while c and c.name != "__root__":
            chain.insert(0, c)
            c = c.parent
        for cg in chain:
            parts.append(f'<a class="el" href="group__{cg.name}{PAGE_EXT}">{E(cg.name)}</a>')
    if parts:
        return '<div class="ingroups">' + ' &#187; '.join(parts) + '</div>'
    return ""

def mem_item_left_right(left, right):
    return f'<tr class="memitem"><td class="memItemLeft">{left}</td><td class="memItemRight">{right}</td></tr>'

def section_header(name, anchor):
    return f"""<tr class="heading"><td colspan="2"><h2 id="header-{anchor}" class="groupheader"><a id="{anchor}" name="{anchor}"></a>
{name}</h2></td></tr>"""

# ────────────────────────────────────────────────────────────────────

class HtmlGenerator:
    def __init__(self, root_group, out_dir):
        self.root = root_group
        self.out = out_dir
        self.out.mkdir(parents=True, exist_ok=True)
        # Assign _group reference to each entity
        for g in root_group.subgroups.values():
            self._assign_groups(g)

    def _assign_groups(self, g):
        for e in g.entities:
            e._group = g
        for sg in g.subgroups.values():
            self._assign_groups(sg)

    def _group_file(self, gname):
        return f"group__{gname}{PAGE_EXT}"

    def _entity_file(self, entity):
        return f"{entity.anchor}{PAGE_EXT}"

    # ── Index Page ──
    def render_index_page(self):
        path = self.out / "index.html"
        content = page_doctype()
        content += page_head("Sensor Data Acquisition Library")
        content += page_titlebar()
        content += nav_tabs("main")
        content += """<div id="doc-content">
<div class="header">
  <div class="headertitle"><div class="title">Sensor Data Acquisition Library </div></div>
</div><!--header-->
<div class="contents">
<div class="textblock">
<p>Embedded C library for sensor drivers and real-time signal processing</p>

<h1><a class="anchor" id="overview"></a>Overview</h1>
<p>This library provides a clean, portable API for interfacing with common
sensor types and processing their data in real time on embedded targets.</p>

<h1><a class="anchor" id="modules"></a>API Modules</h1>
<p>The library is organised into two top-level groups:</p>
<ul>
"""
        for gname, g in sorted(self.root.subgroups.items()):
            if gname.startswith("__"): continue
            content += f'<li><a class="el" href="group__{gname}{PAGE_EXT}">{E(g.brief or gname)}</a></li>\n'
        content += """</ul>

<h1><a class="anchor" id="example"></a>Quick Example</h1>
<div class="fragment"><div class="line">#include "sensor.h"</div>
<div class="line">#include "data_processor.h"</div>
<div class="line"> </div>
<div class="line">int main(void) {</div>
<div class="line">    sensor_config_t scfg;</div>
<div class="line">    sensor_default_config(SENSOR_TYPE_TEMPERATURE, &amp;scfg);</div>
<div class="line">    scfg.sample_rate_hz = 50;</div>
<div class="line"> </div>
<div class="line">    sensor_driver_t *drv = sensor_create(&amp;scfg);</div>
<div class="line">    sensor_start(drv);</div>
<div class="line"> </div>
<div class="line">    ...</div>
<div class="line"> </div>
<div class="line">    sensor_destroy(&amp;drv);</div>
<div class="line">    return 0;</div>
<div class="line">}</div>
</div>
</div></div>"""
        content += page_footer()
        path.write_text(content, encoding=ENCODING)

    # ── Modules Page (Topics) ──
    def render_modules_page(self):
        path = self.out / "modules.html"
        content = page_doctype()
        content += page_head("Topics")
        content += page_titlebar()
        content += nav_tabs("topics")
        content += """<div id="doc-content">
<div class="header">
  <div class="headertitle"><div class="title">Topics</div></div>
</div><!--header-->
<div class="contents">
<div class="textblock"><p>Here is a list of all documented modules:</p></div>
<table class="memberdecls">
<tr class="heading"><td colspan="2"><h2 class="groupheader">Modules</h2></td></tr>
"""
        for gname, g in sorted(self.root.subgroups.items()):
            if gname.startswith("__"): continue
            f = self._group_file(gname)
            content += f'<tr class="memitem"><td class="memItemLeft">&#160;</td><td class="memItemRight"><a class="el" href="{f}">{E(gname)}</a></td></tr>\n'
            if g.brief:
                content += f'<tr class="memdesc:group__{gname}"><td class="mdescLeft">&#160;</td><td class="mdescRight">{E(g.brief)}<br/></td></tr>\n'
        content += "</table></div>"
        content += page_footer()
        path.write_text(content, encoding=ENCODING)

    # ── Files Page ──
    def render_files_page(self):
        path = self.out / "files.html"
        content = page_doctype()
        content += page_head("Files")
        content += page_titlebar()
        content += nav_tabs("files")
        content += """<div id="doc-content">
<div class="header">
  <div class="headertitle"><div class="title">File List</div></div>
</div><!--header-->
<div class="contents">
<div class="textblock"><p>Here is a list of all documented files:</p></div>
<table class="memberdecls">
<tr class="heading"><td colspan="2"><h2 class="groupheader">Files</h2></td></tr>
"""
        for fn in ["sensor.h","data_processor.h","sensor.c","data_processor.c"]:
            content += f'<tr class="memitem"><td class="memItemLeft">&#160;</td><td class="memItemRight"><span class="el">file&#160;<a class="el" href="#">{E(fn)}</a></span></td></tr>\n'
        content += "</table></div>"
        content += page_footer()
        path.write_text(content, encoding=ENCODING)

    # ── Classes / Annotated Page ──
    def render_classes_page(self):
        path = self.out / "annotated.html"
        content = page_doctype()
        content += page_head("Classes")
        content += page_titlebar()
        content += nav_tabs("classes")
        content += """<div id="doc-content">
<div class="header">
  <div class="headertitle"><div class="title">Class List</div></div>
</div><!--header-->
<div class="contents">
<div class="textblock"><p>Here is a list of all documented structures:</p></div>
<table class="memberdecls">
<tr class="heading"><td colspan="2"><h2 class="groupheader">Classes</h2></td></tr>
"""
        structs = []
        for g in self.root.subgroups.values():
            for e in g.flat_entities():
                if e.kind in ("struct",):
                    structs.append(e)
        for e in sorted(structs, key=lambda x: x.name):
            ef = self._entity_file(e)
            brief = e.doc.brief or ""
            content += f'<tr class="memitem"><td class="memItemLeft">&#160;</td><td class="memItemRight"><a class="el" href="{ef}">{E(e.name)}</a></td></tr>\n'
            if brief:
                content += f'<tr class="memdesc:{e.entity_id()}"><td class="mdescLeft">&#160;</td><td class="mdescRight">{E(brief)}<br/></td></tr>\n'
        content += "</table></div>"
        content += page_footer()
        path.write_text(content, encoding=ENCODING)

    # ── Group Page ──
    def render_group_page(self, group):
        if group.name == "__root__": return
        path = self.out / self._group_file(group.name)
        content = page_doctype()
        content += page_head(group.name)

        # Build ingroups breadcrumb
        ingroups = ""
        chain = []
        c = group.parent
        while c and c.name != "__root__":
            chain.insert(0, c)
            c = c.parent
        if chain:
            links = ' &#187; '.join(
                f'<a class="el" href="group__{cg.name}{PAGE_EXT}">{E(cg.name)}</a>'
                for cg in chain
            )
            ingroups = f'<div class="ingroups">{links}</div>'

        content += page_titlebar()
        content += nav_tabs("topics")
        content += f"""<div id="doc-content">
<div class="header">
  <div class="summary">
"""
        # Summary links
        summary_links = []
        if group.subgroups:
            summary_links.append('<a href="#groups">Topics</a>')
        if group.entities:
            cats = set(e.kind for e in group.entities)
            for cat in ["enum","struct","function","typedef"]:
                if cat in cats:
                    summary_links.append(f'<a href="#{cat}-members">{cat.title()}s</a>')
        content += ' &#124; '.join(summary_links) + '\n'
        content += f"""  </div>
  <div class="headertitle"><div class="title">{E(group.name)}{ingroups}</div></div>
</div><!--header-->
<div class="contents">

<p>{E(group.brief)}.  
<a href="#details">More...</a></p>
"""
        # Subgroups table
        if group.subgroups:
            content += """<table class="memberdecls">
<tr class="heading"><td colspan="2"><h2 id="header-groups" class="groupheader"><a id="groups" name="groups"></a>
Topics</h2></td></tr>
"""
            for sg_name, sg in sorted(group.subgroups.items()):
                f = self._group_file(sg_name)
                content += f'<tr class="memitem:{sg_name}"><td class="memItemLeft">&#160;</td><td class="memItemRight"><a class="el" href="{f}">{E(sg_name)}</a></td></tr>\n'
                if sg.brief:
                    content += f'<tr class="memdesc:group__{sg_name}"><td class="mdescLeft">&#160;</td><td class="mdescRight">{E(sg.brief)}<br/></td></tr>\n'
            content += "</table>\n"

        # Entity sections
        if group.entities:
            # Group entities by kind
            cats_order = [("enum","Enumerations","enum-members"),
                          ("struct","Structures","struct-members"),
                          ("function","Functions","func-members"),
                          ("typedef","Typedefs","typedef-members")]
            for kind, title, anchor in cats_order:
                ents = [e for e in group.entities if e.kind == kind]
                if not ents: continue
                content += f"""<table class="memberdecls">
{section_header(title, anchor)}
"""
                for e in ents:
                    ef = self._entity_file(e)
                    brief = e.doc.brief or ""
                    kind_label = kind
                    content += f'<tr class="memitem:{e.entity_id()}"><td class="memItemLeft">{kind_label} &#160;</td><td class="memItemRight"><a class="el" href="{ef}">{E(e.name)}</a></td></tr>\n'
                    if brief:
                        content += f'<tr class="memdesc:{e.entity_id()}"><td class="mdescLeft">&#160;</td><td class="mdescRight">{E(brief)}<br/></td></tr>\n'
                content += "</table>\n"

        # Details
        details_text = group.details or group.brief or ""
        content += f"""<a name="details" id="details"></a><h2 id="header-details" class="groupheader">Detailed Description</h2>
<div class="textblock"><p>{E(details_text)}</p>
</div></div>"""
        content += page_footer()
        path.write_text(content, encoding=ENCODING)

    # ── Entity Detail Page ──
    def render_entity_page(self, entity):
        path = self.out / self._entity_file(entity)
        title = f"{entity.name} — {entity.kind}"
        content = page_doctype()
        content += page_head(title)
        ig = ingroups_breadcrumb(entity)
        content += page_titlebar()

        # Determine which nav tab is active based on kind
        nav = "classes" if entity.kind in ("struct","union") else "topics"
        content += nav_tabs(nav)
        content += f"""<div id="doc-content">
<div class="header">
  <div class="summary">
"""
        # Summary links
        summary = []
        if entity.enum_values:
            summary.append('<a href="#pub-attribs">Enum values</a>')
        if entity.struct_fields:
            summary.append('<a href="#pub-attribs">Public Attributes</a>')
        if entity.func_params:
            summary.append('<a href="#func-params">Parameters</a>')
        content += ' &#124; '.join(summary) + '\n'
        content += f"""  </div>
  <div class="headertitle"><div class="title">{E(entity.name)} {entity.kind.title()} Reference{ig}</div></div>
</div><!--header-->
<div class="contents">

<p>{E(entity.doc.brief)}.  
 <a href="#details">More...</a></p>
"""
        # Source file reference
        content += f"""<p><code>#include &lt;sensor.h&gt;</code></p>
"""

        # Enum values table
        if entity.enum_values:
            rows = ""
            for v in entity.enum_values:
                doc = E(v.doc) if v.doc else ""
                rows += f'<tr class="memitem:{v.name}" id="r_{v.name}"><td class="memItemLeft">{E(v.name)}</td><td class="memItemRight">{E(v.value) if v.value else "&#160;"}</td></tr>\n'
                if doc:
                    rows += f'<tr class="memdesc:{v.name}"><td class="mdescLeft">&#160;</td><td class="mdescRight">{doc}<br/></td></tr>\n'
            content += f"""<table class="memberdecls">
{section_header("Enum Values", "pub-attribs")}
{rows}
</table>
"""

        # Struct fields table
        if entity.struct_fields:
            rows = ""
            for f_ in entity.struct_fields:
                doc = E(f_.doc) if f_.doc else ""
                rows += f'<tr class="memitem:{f_.name}"><td class="memItemLeft">{E(f_.type)}&#160;</td><td class="memItemRight">{E(f_.name)}</td></tr>\n'
                if doc:
                    rows += f'<tr class="memdesc:{f_.name}"><td class="mdescLeft">&#160;</td><td class="mdescRight">{doc}<br/></td></tr>\n'
            content += f"""<table class="memberdecls">
{section_header("Public Attributes", "pub-attribs")}
{rows}
</table>
"""

        # Detailed description
        content += f"""<a name="details" id="details"></a><h2 id="header-details" class="groupheader">Detailed Description</h2>
<div class="textblock"><p>{E(entity.doc.details or entity.doc.brief or "")}</p>
</div>
"""

        # Function full documentation
        if entity.kind == "function":
            content += f"""<a name="doc-func-members" id="doc-func-members"></a>
<h2 class="groupheader">Function Documentation</h2>
<a id="{entity.entity_id()}" name="{entity.entity_id()}"></a>
<h2 class="memtitle"><span class="permalink"><a href="#{entity.entity_id()}">&#9670;&#160;</a></span>{entity.name}()</h2>

<div class="memitem">
<div class="memproto">
      <table class="memname">
        <tr>
          <td class="memname">{E(entity.func_return)} {entity.name} </td>
          <td>(</td>
"""
            # Params in memproto style
            for i, p in enumerate(entity.func_params):
                sep = "," if i < len(entity.func_params) - 1 else ""
                content += f'          <td class="paramtype">{E(p.type)}</td>\n'
                content += f'          <td class="paramname"><em>{E(p.name)}</em></td><td>)</td>\n'
            if not entity.func_params:
                content += '          <td class="paramname"></td><td>)</td>\n'
            content += """        </tr>
      </table>
</div><div class="memdoc">
"""
            if entity.doc.brief:
                content += f"<p>{E(entity.doc.brief)}</p>\n"
            # Parameters docs
            if entity.func_params:
                content += '<dl class="params"><dt>Parameters</dt><dd>\n  <table class="params">\n'
                content += '    <tr><th>Direction</th><th>Name</th><th>Description</th></tr>\n'
                for p in entity.func_params:
                    dir_map = {"in":"[in]","out":"[out]","inout":"[in,out]"}
                    d = dir_map.get(p.direction, "[in]")
                    content += f'    <tr><td class="paramdir">{d}</td><td class="paramname">{E(p.name)}</td><td>{E(p.doc)}</td></tr>\n'
                content += '  </table>\n</dd></dl>\n'
            # Return
            if entity.doc.return_:
                content += f'<dl class="section return"><dt>Returns</dt><dd>{E(entity.doc.return_)}</dd></dl>\n'
            # Retvals
            if entity.doc.retvals:
                content += '<dl class="retval"><dt>Return values</dt><dd>\n  <table class="retval">\n'
                for code, desc in entity.doc.retvals:
                    content += f'    <tr><td class="paramname">{E(code)}</td><td>{E(desc)}</td></tr>\n'
                content += '  </table>\n</dd></dl>\n'
            # Pre/Post
            if entity.doc.pre:
                content += f'<dl class="section pre"><dt>Precondition</dt><dd>{E(entity.doc.pre)}</dd></dl>\n'
            if entity.doc.post:
                content += f'<dl class="section post"><dt>Postcondition</dt><dd>{E(entity.doc.post)}</dd></dl>\n'
            if entity.doc.note:
                content += f'<dl class="section note"><dt>Note</dt><dd>{E(entity.doc.note)}</dd></dl>\n'
            if entity.doc.warning:
                content += f'<dl class="section warning"><dt>Warning</dt><dd>{E(entity.doc.warning)}</dd></dl>\n'
            content += "</div></div>\n"

        content += "</div>"
        content += page_footer()
        path.write_text(content, encoding=ENCODING)

    # ── CSS ──
    def render_css(self):
        # Read Doxygen's CSS from docs_doxygen
        src = Path("docs_doxygen") / "html" / "doxygen.css"
        dst = self.out / "doxygen.css"
        if src.exists():
            dst.write_bytes(src.read_bytes())
        else:
            # Minimal fallback
            self._write_minimal_css(dst)

        # tabs.css
        src2 = Path("docs_doxygen") / "html" / "tabs.css"
        dst2 = self.out / "tabs.css"
        if src2.exists():
            dst2.write_bytes(src2.read_bytes())
        else:
            self._write_minimal_tabs(dst2)

    def _write_minimal_css(self, path):
        path.write_text("""body { background-color: white; color: black; font-family: system-ui,sans-serif; font-size: 14px; }
a { color: #3D578C; text-decoration: none; }
a.el { font-weight: bold; }
#titlearea { border-bottom: 1px solid #5373B4; background-color: white; padding: 8px; }
#projectname { font-size: 200%; font-weight: normal; }
#projectnumber { font-size: 60%; }
#projectbrief { font-size: 90%; color: #777; }
#doc-content { padding: 12px; }
.header { background-color: #F9FAFC; border-bottom: 1px solid #C4CFE5; padding: 8px; }
.headertitle { font-size: 160%; font-weight: 400; }
.ingroups { font-size: 75%; color: #777; }
.contents { padding: 8px; }
table.memberdecls { width: 100%; border-collapse: collapse; }
td.memItemLeft { padding: 2px 8px; white-space: nowrap; vertical-align: top; background-color: #F9FAFC; }
td.memItemRight { padding: 2px 8px; vertical-align: top; background-color: #F9FAFC; }
td.mdescLeft { padding: 2px 8px; font-size: 12px; color: #777; background-color: #FAFAFA; }
td.mdescRight { padding: 2px 8px; font-size: 12px; color: #777; background-color: #FAFAFA; }
h2.groupheader { color: #354C7B; font-size: 150%; font-weight: normal; border-bottom: 1px solid #C4CFE5; padding: 4px 0; }
div.textblock { max-width: 1000px; }
dl.params, dl.section, dl.retval { margin: 8px 0; }
dl.params dt, dl.section dt, dl.retval dt { font-weight: bold; }
div.memproto { border: 1px solid #C4CFE5; border-radius: 4px; background-color: #FBFCFD; padding: 8px; }
div.memdoc { padding: 8px; border-left: 2px solid #C4CFE5; margin-bottom: 16px; }
table.memname { width: 100%; }
td.paramtype { font-style: italic; }
td.paramname { font-weight: bold; }
h2.memtitle { font-size: 130%; border-bottom: 1px solid #C4CFE5; padding-bottom: 4px; }
.permalink { font-size: 70%; }
hr.footer { border: none; border-top: 1px solid #C4CFE5; }
address.footer { font-size: 12px; color: #777; text-align: center; padding: 8px; }
div.fragment { border: 1px solid #C4CFE5; border-radius: 4px; background-color: #FBFCFD; padding: 10px; font-family: monospace; }
div.line { font-family: monospace; line-height: 1.3; }
""", encoding=ENCODING)

    def _write_minimal_tabs(self, path):
        path.write_text("""body { font-family: system-ui,sans-serif; }
.tabs, .tabs2 { background-color: white; width: 100%; display: table; }
.tablist { margin: 0; padding: 0; display: block; }
.tablist li { float: left; display: table-cell; background-color: white; line-height: 36px; list-style: none; }
.tablist a { display: block; margin: 5px 0; padding: 0px 20px; color: #283A5D; text-decoration: none; }
.tablist li.current a { background-color: #DCE2EF; border-radius: 6px 6px 0 0; }
""", encoding=ENCODING)

    def render_all(self):
        self.render_css()
        self.render_index_page()
        self.render_modules_page()
        self.render_files_page()
        self.render_classes_page()

        def walk(g):
            self.render_group_page(g)
            for sg in g.subgroups.values():
                walk(sg)
            for e in g.entities:
                self.render_entity_page(e)

        for sg in self.root.subgroups.values():
            walk(sg)


# ────────────────────────────────────────────────────────────────────
# CHM Generator
# ────────────────────────────────────────────────────────────────────

class ChmGenerator:
    def __init__(self, root_group, html_dir, chm_path):
        self.root = root_group
        self.html_dir = html_dir
        self.chm_path = Path(chm_path)

    def _hhp_path(self):
        return self.html_dir / "project.hhp"

    def generate_hhp(self):
        content = f"""[OPTIONS]
Compatibility=1.1 or later
Compiled file={self.chm_path.resolve()}
Contents file=project.hhc
Index file=project.hhk
Default topic=index.html
Title={PROJECT_NAME}
Language=0x409 English (United States)
Display compile progress=Yes
Full-text search=Yes
Auto Index=Yes

[FILES]
style.css
index.html
modules.html
files.html
annotated.html
"""
        files_added = {"index.html","modules.html","files.html","annotated.html","style.css"}
        for f in sorted(self.html_dir.glob("*.html")):
            if f.name not in files_added:
                content += f"{f.name}\n"
                files_added.add(f.name)
        content += "\n[INFOTYPES]\n"
        (self.html_dir / "project.hhp").write_text(content, encoding=ENCODING)

    def generate_hhc(self):
        lines = [
            '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">',
            "<HTML><HEAD></HEAD><BODY>",
            '<OBJECT type="text/site properties">',
            '  <param name="Window Styles" value="0x800025">',
            "</OBJECT>",
        ]

        def walk(g, level):
            indent = "  " * (level + 1)
            if g.name == "__root__":
                for sg in g.subgroups.values():
                    yield from walk(sg, 0)
                return
            fname = f"group__{g.name}.html"
            yield (level, g.name or "Modules", fname)
            for sg in g.subgroups.values():
                yield from walk(sg, level + 1)

        items = list(walk(self.root, 0))

        # Build tree
        current_level = 0
        for level, name, local in items:
            if level > current_level:
                lines.append("  " * (current_level + 1) + "<UL>")
            elif level < current_level:
                for _ in range(current_level - level):
                    lines.append("  " * current_level + "</UL>")
            current_level = level
            lines.append(f'  {"  " * level}<LI><OBJECT type="text/sitemap">')
            lines.append(f'  {"  " * level}  <param name="Name" value="{E(name)}">')
            lines.append(f'  {"  " * level}  <param name="Local" value="{local}">')
            lines.append(f'  {"  " * level}</OBJECT>')

        for _ in range(current_level + 1):
            lines.append("  " * current_level + "</UL>")
            current_level -= 1

        lines.append("</BODY></HTML>")
        (self.html_dir / "project.hhc").write_text("\n".join(lines), encoding=ENCODING)

    def generate_hhk(self):
        lines = [
            '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">',
            "<HTML><HEAD></HEAD><BODY>",
            '<OBJECT type="text/site properties">',
            '  <param name="Window Styles" value="0x800025">',
            "</OBJECT>",
        ]
        for gname, g in self.root.subgroups.items():
            if gname.startswith("__"): continue
            fname = f"group__{gname}.html"
            lines.append(f'<LI><OBJECT type="text/sitemap">')
            lines.append(f'  <param name="Name" value="{E(gname)}">')
            lines.append(f'  <param name="Local" value="{fname}">')
            lines.append(f'</OBJECT>')
            for e in g.flat_entities():
                ef = f"{e.anchor}.html"
                lines.append(f'<LI><OBJECT type="text/sitemap">')
                lines.append(f'  <param name="Name" value="{E(e.name)}">')
                lines.append(f'  <param name="Local" value="{ef}">')
                lines.append(f'</OBJECT>')
        lines.append("</BODY></HTML>")
        (self.html_dir / "project.hhk").write_text("\n".join(lines), encoding=ENCODING)

    def compile(self):
        self.generate_hhp()
        self.generate_hhc()
        self.generate_hhk()

        import subprocess
        hhp = self._hhp_path()
        print(f"🔄 Compiling CHM via hhc.exe...")
        try:
            r = subprocess.run([HHC, str(hhp)], capture_output=True, text=True, timeout=60)
            if r.returncode != 0 and r.returncode != 1:
                print(f"❌ hhc.exe failed (rc={r.returncode})")
                print(f"stdout: {r.stdout[:500]}")
                print(f"stderr: {r.stderr[:500]}")
                return False
            print(f"✅ CHM generated: {self.chm_path.resolve()} ({self.chm_path.stat().st_size:,} bytes)")
            return True
        except FileNotFoundError:
            print(f"❌ hhc.exe not found at: {HHC}")
            return False
        except subprocess.TimeoutExpired:
            print("❌ hhc.exe timed out")
            return False


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
            for f in sorted(full.glob("*.h")):
                print(f"  📄 Parsing: {f}")
                parser.parse_file(f)
            for f in sorted(full.glob("*.c")):
                print(f"  📄 Parsing: {f}")
                parser.parse_file(f)

    total_entities = sum(1 for _ in parser.root.flat_entities())
    total_groups = len([g for g in parser.groups if not g.startswith("__")])
    print(f"\n  📊 Parsed: {total_groups} groups, {total_entities} entities")

    print("\n  🎨 Generating HTML pages...")
    html_dir = src_root / OUT_DIR
    hgen = HtmlGenerator(parser.root, html_dir)
    hgen.render_all()
    html_count = len(list(html_dir.glob("*.html")))
    print(f"  ✅ {html_count} HTML pages generated in {html_dir}")

    print("\n  📚 Generating CHM project files...")
    chm_path = src_root / CHM_FILE
    chm = ChmGenerator(parser.root, html_dir, chm_path)
    chm.compile()

    print("\n" + "=" * 60)
    print("  Done.")
    print(f"  HTML:  {html_dir.resolve()}")
    print(f"  CHM:   {chm_path.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
