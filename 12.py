import re
import os
import shutil
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# ===================== 全局配置 =====================
PROJECT_ROOT = r"./src"
OUT_HTML = "./doxygen_style_html"
CHM_FILE_NAME = "C_API_Document.chm"
FILTER_STATIC_FUNC = True
THEME_COLOR = "#2980b9"
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
    funcs: List[FuncInfo] = field(default_factory=list)
    structs: List[StructInfo] = field(default_factory=list)
    enums: List[EnumInfo] = field(default_factory=list)

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

# C语法解析
FUNC_REG    = re.compile(r'(static\s+)?([\w\s\*]+?)\s+(\w+)\s*\(.*?\)\s*;', re.S)
STRUCT_REG  = re.compile(r'typedef\s+struct\s*\{(.*?)\}\s*(\w+)\s*;', re.S)
ENUM_REG    = re.compile(r'typedef\s+enum\s*\{(.*?)\}\s*(\w+)\s*;', re.S)

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
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    file_api = FileApi(file_path=filepath)
    blocks = COMMENT_BLOCK.finditer(content)

    for block in blocks:
        comment_text = block.group(1)
        pos_end = block.end()
        remain = content[pos_end:pos_end+1000]
        info = parse_comment(comment_text)

        # 文件注释
        if "@file" in comment_text:
            file_api.file_brief = info["brief"]
            file_api.file_author = info["author"]
            file_api.file_date = info["date"]

        # 函数
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

        # 结构体
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

        # 枚举
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

def scan_all_project() -> List[FileApi]:
    all_files = []
    for root, _, files in os.walk(PROJECT_ROOT):
        for name in files:
            if name.endswith((".h", ".c")):
                fp = os.path.join(root, name)
                all_files.append(parse_file(fp))
    return all_files

# -------------------------- Doxygen 原版风格 HTML 生成 --------------------------
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
    """

    # 首页
    index_html = [
        f'<html><head><meta charset=utf-8><style>{css_style}</style></head>',
        '<div class="header">C Language API Document</div>',
        '<div class="container">',
        '<h2>工程文件目录</h2><hr>'
    ]

    for fileinfo in all_api:
        fname = os.path.basename(fileinfo.file_path)
        html_name = fname.replace(".", "_") + ".html"
        index_html.append(f'<p>📄 <a href="{html_name}">{fileinfo.file_path}</a></p>')

        # 单文件页面
        page = [
            f'<html><head><meta charset=utf-8><style>{css_style}</style></head>',
            f'<div class="header">API Detail Document</div>',
            '<div class="container">',
            f'<h3>文件路径：{fileinfo.file_path}</h3>',
            f'<p>简介：{fileinfo.file_brief}</p>',
            f'<p>作者：{fileinfo.file_author}　日期：{fileinfo.file_date}</p>',
            '<p><a href="index.html">← 返回主页</a></p><hr>'
        ]

        # 函数
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

                page.append(f'<div class="code">{f.raw_code}</div>')
                page.append('</div>')

        # 结构体
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

        # 枚举
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
        with open(os.path.join(OUT_HTML, html_name), "w", encoding="utf-8") as f:
            f.write("\n".join(page))

    index_html.append('</div></html>')
    with open(os.path.join(OUT_HTML, "index.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(index_html))

# -------------------------- 生成标准CHM工程文件（完整目录+搜索索引） --------------------------
def build_full_chm_project():
    html_dir = OUT_HTML
    chm_out = os.path.abspath(CHM_FILE_NAME)

    # HHP 工程配置
    hhp_text = f"""[OPTIONS]
Compatibility=1.1 or later
Compiled file={chm_out}
Contents file=table.hhc
Index file=keyword.hhk
Default topic=index.html
Title=C语言API接口文档
Default Window=mainwin
Language=0x804

[WINDOWS]
mainwin="index.html,table.hhc,keyword.hhk,,,,,0,0,0,0,,0,0,0"

[FILES]
*.html
"""
    with open(os.path.join(html_dir, "project.hhp"), "w", encoding="gbk") as f:
        f.write(hhp_text)

    # HHC 左侧树形目录（可折叠分级）
    toc = ['<HTML><BODY><UL>']
    toc.append(r'''
<LI><OBJECT type="text/sitemap">
<param name="Name" value="文档首页">
<param name="Local" value="index.html">
</OBJECT>
''')
    for name in sorted(os.listdir(html_dir)):
        if name.endswith(".html") and name != "index.html":
            disp_name = name.replace("_", "/").replace(".html","")
            toc.append(f'''
<LI><OBJECT type="text/sitemap">
<param name="Name" value="{disp_name}">
<param name="Local" value="{name}">
</OBJECT>
''')
    toc.append('</UL></BODY></HTML>')
    with open(os.path.join(html_dir, "table.hhc"), "w", encoding="gbk") as f:
        f.write("\n".join(toc))

    # HHK 全文搜索索引
    idx = '''<HTML><BODY><UL></UL></BODY></HTML>'''
    with open(os.path.join(html_dir, "keyword.hhk"), "w", encoding="gbk") as f:
        f.write(idx)

# -------------------------- 编译CHM --------------------------
def compile_final_chm():
    import subprocess
    old_path = os.getcwd()
    os.chdir(OUT_HTML)
    try:
        subprocess.run(["hhc.exe", "project.hhp"], shell=True, check=True)
        print(f"\n✅ 最终 CHM 文档生成成功：{CHM_FILE_NAME}")
    except Exception:
        print("\n⚠️  请安装 HTML Help Workshop，并把安装目录加入系统PATH环境变量")
    os.chdir(old_path)

if __name__ == "__main__":
    print("【1/4】正在深度解析C代码与Doxygen注释...")
    api_data = scan_all_project()
    print(f"【2/4】解析完成，共读取 {len(api_data)} 个代码文件")

    print("【3/4】生成Doxygen风格标准化HTML页面...")
    build_doxygen_html(api_data)

    print("【4/4】构建CHM目录树、搜索索引、编译帮助文档...")
    build_full_chm_project()
    compile_final_chm()
