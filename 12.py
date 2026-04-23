import re
import os
import shutil
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set

# ===================== 全局配置 =====================
PROJECT_ROOT = r"./src"
OUT_HTML = "./doxygen_full_html"
CHM_FILE_NAME = "C_API_Full_Doc.chm"
FILTER_STATIC_FUNC = True
THEME_COLOR = "#2980b9"
GEN_CALL_GRAPH = True

# 编码全局统一配置
CODE_READ_ENCODING = ["utf-8", "gbk", "gb2312"]
HTML_ENCODING = "utf-8"
CHM_FILE_ENCODING = "gbk"
# ====================================================

@dataclass
class ParamInfo:
    name: str
    mode: str
    desc: str

@dataclass
class FuncInfo:
    name: str
    return_type: str
    brief: str
    details: str
    params: List[ParamInfo]
    return_desc: str
    note: str
    warning: str
    author: str
    date: str
    deprecated: str
    see: str
    is_static: bool
    raw_code: str
    call_in: Set[str] = field(default_factory=set)
    call_out: Set[str] = field(default_factory=set)

@dataclass
class StructMember:
    name: str
    type: str
    desc: str

@dataclass
class StructInfo:
    name: str
    brief: str
    details: str
    members: List[StructMember]

@dataclass
class EnumItem:
    name: str
    value: str
    desc: str

@dataclass
class EnumInfo:
    name: str
    brief: str
    details: str
    items: List[EnumItem]

@dataclass
class FileApi:
    file_path: str
    file_brief: str = ""
    file_author: str = ""
    file_date: str = ""
    folder_group: str = ""
    funcs: List[FuncInfo] = field(default_factory=list)
    structs: List[StructInfo] = field(default_factory=list)
    enums: List[EnumInfo] = field(default_factory=list)

# 自动兼容读取任意编码文件，彻底解决中文乱码
def safe_read_file(path):
    for enc in CODE_READ_ENCODING:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except:
            continue
    with open(path, "r", encoding="latin-1") as f:
        return f.read()

# -------------------------- Doxygen 全标签正则 --------------------------
COMMENT_BLOCK = re.compile(r'/\*\*(.*?)\*/', re.S)
TAG_BRIEF     = re.compile(r'@brief\s+(.*?)(?=@|$)', re.S)
TAG_DETAILS   = re.compile(r'@details\s+(.*?)(?=@|$)', re.S)
TAG_PARAM     = re.compile(r'@param\[(in|out|inout)\]\s+(\w+)\s+(.*?)(?=@|$)', re.S)
TAG_RETURN    = re.compile(r'@return\s+(.*?)(?=@|$)', re.S)
TAG_NOTE      = re.compile(r'@note\s+(.*?)(?=@|$)', re.S)
TAG_WARN      = re.compile(r'@warning\s+(.*?)(?=@|$)', re.S)
TAG_AUTHOR    = re.compile(r'@author\s+(.*?)(?=@|$)', re.S)
TAG_DATE      = re.compile(r'@date\s+(.*?)(?=@|$)', re.S)
TAG_DEPRECATE = re.compile(r'@deprecated\s+(.*?)(?=@|$)', re.S)
TAG_SEE       = re.compile(r'@see\s+(.*?)(?=@|$)', re.S)

FUNC_REG    = re.compile(r'(static\s+)?([\w\s\*]+?)\s+(\w+)\s*\(.*?\)\s*;', re.S)
STRUCT_REG  = re.compile(r'typedef\s+struct\s*\{(.*?)\}\s*(\w+)\s*;', re.S)
ENUM_REG    = re.compile(r'typedef\s+enum\s*\{(.*?)\}\s*(\w+)\s*;', re.S)
CALL_REG    = re.compile(r'(\w+)\s*\(', re.S)

def parse_comment(text: str):
    return {
        "brief": TAG_BRIEF.search(text).group(1).strip() if TAG_BRIEF.search(text) else "",
        "details": TAG_DETAILS.search(text).group(1).strip() if TAG_DETAILS.search(text) else "",
        "params": [ParamInfo(m[1], m[0].strip(), m[2].strip()) for m in TAG_PARAM.findall(text)],
        "return": TAG_RETURN.search(text).group(1).strip() if TAG_RETURN.search(text) else "",
        "note": TAG_NOTE.search(text).group(1).strip() if TAG_NOTE.search(text) else "",
        "warning": TAG_WARN.search(text).group(1).strip() if TAG_WARN.search(text) else "",
        "author": TAG_AUTHOR.search(text).group(1).strip() if TAG_AUTHOR.search(text) else "",
        "date": TAG_DATE.search(text).group(1).strip() if TAG_DATE.search(text) else "",
        "deprecated": TAG_DEPRECATE.search(text).group(1).strip() if TAG_DEPRECATE.search(text) else "",
        "see": TAG_SEE.search(text).group(1).strip() if TAG_SEE.search(text) else "",
    }

def parse_file(filepath: str) -> FileApi:
    content = safe_read_file(filepath)
    file_api = FileApi(file_path=filepath)
    file_api.folder_group = os.path.dirname(os.path.relpath(filepath, PROJECT_ROOT))
    blocks = COMMENT_BLOCK.finditer(content)

    for block in blocks:
        comment_text = block.group(1)
        pos_end = block.end()
        remain = content[pos_end:pos_end+1000]
        info = parse_comment(comment_text)

        if "@file" in comment_text:
            file_api.file_brief = info["brief"]
            file_api.file_author = info["author"]
            file_api.file_date = info["date"]

        func_match = FUNC_REG.search(remain)
        if func_match:
            is_static = bool(func_match.group(1))
            ret_type = func_match.group(2).strip()
            func_name = func_match.group(3)

            func = FuncInfo(
                name=func_name,
                return_type=ret_type,
                brief=info["brief"],
                details=info["details"],
                params=info["params"],
                return_desc=info["return"],
                note=info["note"],
                warning=info["warning"],
                author=info["author"],
                date=info["date"],
                deprecated=info["deprecated"],
                see=info["see"],
                is_static=is_static,
                raw_code=func_match.group(0).strip()
            )
            file_api.funcs.append(func)

        struct_match = STRUCT_REG.search(remain)
        if struct_match:
            body, name = struct_match.groups()
            members = []
            for line in body.splitlines():
                line = line.strip()
                if not line or line.startswith("//"):
                    continue
                m = re.search(r'([\w\*]+)\s+(\w+)', line)
                if m:
                    members.append(StructMember(type=m.group(1), name=m.group(2), desc=""))
            st = StructInfo(name=name, brief=info["brief"], details=info["details"], members=members)
            file_api.structs.append(st)

        enum_match = ENUM_REG.search(remain)
        if enum_match:
            body, name = enum_match.groups()
            items = []
            for line in body.split(","):
                line = line.strip()
                if not line:
                    continue
                kv = re.match(r'(\w+)\s*=\s*([0-9A-Fx]+)', line)
                if kv:
                    items.append(EnumItem(name=kv.group(1), value=kv.group(2), desc=""))
            en = EnumInfo(name=name, brief=info["brief"], details=info["details"], items=items)
            file_api.enums.append(en)

    return file_api

def build_call_relation(all_api: List[FileApi]):
    func_map = {}
    all_func_names = set()
    for fapi in all_api:
        for func in fapi.funcs:
            func_map[func.name] = func
            all_func_names.add(func.name)

    for fapi in all_api:
        code = safe_read_file(fapi.file_path)
        called = CALL_REG.findall(code)
        for func in fapi.funcs:
            for call_name in called:
                if call_name in all_func_names and call_name != func.name:
                    func.call_out.add(call_name)
                    if call_name in func_map:
                        func_map[call_name].call_in.add(func.name)

def scan_all_project() -> List[FileApi]:
    all_files = []
    for root, _, files in os.walk(PROJECT_ROOT):
        for name in files:
            if name.endswith((".h", ".c")):
                fp = os.path.join(root, name)
                all_files.append(parse_file(fp))
    if GEN_CALL_GRAPH:
        build_call_relation(all_files)
    return all_files

# -------------------------- Doxygen 原版风格 HTML 强制UTF8编码 --------------------------
def build_doxygen_html(all_api: List[FileApi]):
    if os.path.exists(OUT_HTML):
        shutil.rmtree(OUT_HTML)
    os.makedirs(OUT_HTML, exist_ok=True)

    css_style = f"""
    body{{font-family:"Microsoft Yahei",Arial;font-size:14px;margin:0;padding:0;background:#fff;color:#333}}
    .header{{background:{THEME_COLOR};color:white;padding:14px 20px;font-size:18px;font-weight:bold}}
    .container{{padding:20px 30px}}
    .title{{font-size:16px;font-weight:bold;color:{THEME_COLOR};border-bottom:2px solid {THEME_COLOR};padding:6px 0;margin:15px 0}}
    .func-box{{border:1px solid #e0e0e0;border-radius:4px;padding:16px;margin:12px 0;background:#fafcff}}
    .code{{background:#f5f5f5;padding:10px;border-radius:3px;font-family:Consolas}}
    .warn{{color:#c0392b}}
    .note{{color:#27ae60}}
    .deprecated{{color:#888;text-decoration:line-through}}
    .graph{{background:#f0f8ff;padding:10px;border-left:4px solid {THEME_COLOR};margin:8px 0}}
    """

    group_dict = defaultdict(list)
    for item in all_api:
        group_dict[item.folder_group].append(item)

    index_html = [
        f'<html><head><meta charset="UTF-8"><style>{css_style}</style></head>',
        '<div class="header">C Language API Full Document</div>',
        '<div class="container">',
        '<h2>工程模块目录（自动分组）</h2><hr>'
    ]

    for folder, file_list in sorted(group_dict.items()):
        index_html.append(f'<h3>📂 {folder}</h3>')
        for fileinfo in file_list:
            fname = os.path.basename(fileinfo.file_path)
            html_name = fname.replace(".", "_") + ".html"
            index_html.append(f'<p>　└ 📄 <a href="{html_name}">{os.path.basename(fileinfo.file_path)}</p>')

            page = [
                f'<html><head><meta charset="UTF-8"><style>{css_style}</style></head>',
                f'<div class="header">API Detail Document</div>',
                '<div class="container">',
                f'<h3>文件：{fileinfo.file_path}</h3>',
                f'<p>模块分组：{fileinfo.folder_group}</p>',
                f'<p>简介：{fileinfo.file_brief}</p>',
                f'<p>作者：{fileinfo.file_author}　日期：{fileinfo.file_date}</p>',
                '<p><a href="index.html">← 返回主页</a></p><hr>'
            ]

            if fileinfo.funcs:
                page.append('<div class="title">函数接口</div>')
                for f in fileinfo.funcs:
                    if FILTER_STATIC_FUNC and f.is_static:
                        continue
                    page.append('<div class="func-box">')
                    page.append(f'<b>{f.return_type} {f.name}</b>')
                    page.append(f'<p><strong>简要说明：</strong>{f.brief}</p>')
                    if f.details:
                        page.append(f'<p><strong>详细描述：</strong>{f.details}</p>')
                    if f.deprecated:
                        page.append(f'<p class="deprecated">已废弃：{f.deprecated}</p>')

                    if f.params:
                        page.append('<p><strong>参数列表</strong></p><ul>')
                        for p in f.params:
                            page.append(f'<li>[{p.mode}] {p.name} : {p.desc}</li>')
                        page.append('</ul>')

                    if f.return_desc:
                        page.append(f'<p><strong>返回值：</strong>{f.return_desc}</p>')
                    if f.note:
                        page.append(f'<p class="note">📌 备注：{f.note}</p>')
                    if f.warning:
                        page.append(f'<p class="warn">⚠️ 警告：{f.warning}</p>')
                    if f.see:
                        page.append(f'<p>参考：{f.see}</p>')

                    if GEN_CALL_GRAPH:
                        page.append('<div class="graph">')
                        page.append('<strong>调用关系</strong>')
                        page.append(f'<p>调用其他函数：{"、".join(f.call_out) if f.call_out else "无"}</p>')
                        page.append(f'<p>被以下函数调用：{"、".join(f.call_in) if f.call_in else "无"}</p>')
                        page.append('</div>')

                    page.append(f'<div class="code">{f.raw_code}</div>')
                    page.append('</div>')

            if fileinfo.structs:
                page.append('<div class="title">结构体定义</div>')
                for s in fileinfo.structs:
                    page.append('<div class="func-box">')
                    page.append(f'<b>struct {s.name}</b>')
                    page.append(f'<p>{s.brief} {s.details}</p>')
                    page.append('<ul>')
                    for m in s.members:
                        page.append(f'<li>{m.type}　{m.name}</li>')
                    page.append('</ul></div>')

            if fileinfo.enums:
                page.append('<div class="title">枚举类型</div>')
                for e in fileinfo.enums:
                    page.append('<div class="func-box">')
                    page.append(f'<b>enum {e.name}</b>')
                    page.append(f'<p>{e.brief}</p>')
                    page.append('<ul>')
                    for item in e.items:
                        page.append(f'<li>{item.name} = {item.value}</li>')
                    page.append('</ul></div>')

            page.append('</div></html>')
            with open(os.path.join(OUT_HTML, html_name), "w", encoding=HTML_ENCODING) as f:
                f.write("\n".join(page))

    index_html.append('</div></html>')
    with open(os.path.join(OUT_HTML, "index.html"), "w", encoding=HTML_ENCODING) as f:
        f.write("\n".join(index_html))

# -------------------------- CHM 文件强制GBK编码，彻底解决CHM中文乱码 --------------------------
def build_full_chm_project(all_api: List[FileApi]):
    html_dir = OUT_HTML
    chm_out = os.path.abspath(CHM_FILE_NAME)

    hhp_text = f"""[OPTIONS]
Compatibility=1.1 or later
Compiled file={chm_out}
Contents file=table.hhc
Index file=keyword.hhk
Default topic=index.html
Title=C语言API完整文档
Default Window=mainwin
Language=0x804

[WINDOWS]
mainwin="index.html,table.hhc,keyword.hhk,,,,,0,0,0,0,,0,0,0"

[FILES]
*.html
"""
    with open(os.path.join(html_dir, "project.hhp"), "w", encoding=CHM_FILE_ENCODING) as f:
        f.write(hhp_text)

    toc = ['<HTML><BODY><UL>']
    toc.append(r'''
<LI><OBJECT type="text/sitemap">
<param name="Name" value="文档首页">
<param name="Local" value="index.html">
</OBJECT>
''')

    group_dict = defaultdict(list)
    for item in all_api:
        group_dict[item.folder_group].append(item)

    for folder, file_list in sorted(group_dict.items()):
        toc.append(f'<LI><OBJECT type="text/sitemap"><param name="Name" value="{folder}"></OBJECT><UL>')
        for fileinfo in file_list:
            name = os.path.basename(fileinfo.file_path).replace(".", "_") + ".html"
            disp = os.path.basename(fileinfo.file_path)
            toc.append(f'''
<LI><OBJECT type="text/sitemap">
<param name="Name" value="{disp}">
<param name="Local" value="{name}">
</OBJECT>
''')
        toc.append('</UL>')
    toc.append('</UL></BODY></HTML>')
    with open(os.path.join(html_dir, "table.hhc"), "w", encoding=CHM_FILE_ENCODING) as f:
        f.write("\n".join(toc))

    keywords = set()
    for fapi in all_api:
        for func in fapi.funcs:
            keywords.add(func.name)
        for st in fapi.structs:
            keywords.add(st.name)
        for en in fapi.enums:
            keywords.add(en.name)

    hhk = ['<HTML><BODY><UL>']
    for word in sorted(keywords):
        hhk.append(f'''
<LI><OBJECT type="text/keyword">
<param name="Name" value="{word}">
<param name="Local" value="index.html">
</OBJECT>
''')
    hhk.append('</UL></BODY></HTML>')
    with open(os.path.join(html_dir, "keyword.hhk"), "w", encoding=CHM_FILE_ENCODING) as f:
        f.write("\n".join(hhk))

# -------------------------- 编译CHM --------------------------
def compile_final_chm():
    import subprocess
    old_path = os.getcwd()
    os.chdir(OUT_HTML)
    try:
        subprocess.run(["hhc.exe", "project.hhp"], shell=True, check=True)
        print(f"\n✅ CHM 完整文档生成完成：{CHM_FILE_NAME}")
    except Exception as e:
        print(f"\n⚠️ CHM编译提示：{e}")
        print("请确认已安装 HTML Help Workshop 并配置环境变量")
    os.chdir(old_path)

if __name__ == "__main__":
    print("【1/5】解析C代码与Doxygen注释（多编码兼容）...")
    api_data = scan_all_project()
    print(f"【2/5】读取文件：{len(api_data)} 个")

    print("【3/5】分析函数调用关系图...")
    print("【4/5】生成UTF8标准网页文档...")
    build_doxygen_html(api_data)

    print("【5/5】GBK编码构建CHM目录索引，编译帮助文档...")
    build_full_chm_project(api_data)
    compile_final_chm()
