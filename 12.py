import os
import re
import subprocess

# ====================== 配置区（你只需要改这里） ======================
HHC_PATH = r"C:\Program Files (x86)\HTML Help Workshop\hhc.exe"
HEADER_FOLDER = r"C:\Users\jamie\PycharmProjects\PythonProject\seafile-master"
OUTPUT_DIR = "chm_output_final"
CHM_NAME = "all_functions.chm"
# =====================================================================

# ---------------------------------------------------------------------
# 解析 结构体 struct（提取整块代码 + 保留格式）
# ---------------------------------------------------------------------
def parse_structs(content):
    structs = []
    pattern = re.compile(r'(typedef\s+struct\s*\{.*?\}\s*\w+;)', re.DOTALL)
    for match in pattern.findall(content):
        full_struct = match.strip()
        name = ""
        name_match = re.search(r'\}\s*(\w+);', full_struct)
        if name_match:
            name = name_match.group(1)
        structs.append({
            "name": name,
            "full_code": full_struct
        })
    return structs

# ---------------------------------------------------------------------
# 解析 枚举 enum（提取整块代码 + 保留格式）
# ---------------------------------------------------------------------
def parse_enums(content):
    enums = []
    pattern = re.compile(r'(typedef\s+enum\s*\{.*?\}\s*\w+;)', re.DOTALL)
    for match in pattern.findall(content):
        full_enum = match.strip()
        name = ""
        name_match = re.search(r'\}\s*(\w+);', full_enum)
        if name_match:
            name = name_match.group(1)
        enums.append({
            "name": name,
            "full_code": full_enum
        })
    return enums

# ---------------------------------------------------------------------
# 解析单个头文件（函数 + 结构体 + 枚举）
# ---------------------------------------------------------------------
def parse_single_header(file_path):
    functions = []
    structs = []
    enums = []

    func_pattern = re.compile(
        r'(/\*\*.*?\*/\s*)?(\w+)\s+(\w+)\s*\((.*?)\)\s*;',
        re.DOTALL | re.MULTILINE
    )

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except:
        return [], [], []

    structs = parse_structs(content)
    enums = parse_enums(content)

    matches = func_pattern.findall(content)
    for match in matches:
        comment_block, return_type, func_name, params_str = match
        description = f"{func_name}函数"
        detail = ""
        params = []
        return_desc = ""

        if comment_block:
            comment = comment_block.strip("/** */").strip()
            lines = [l.strip("* ").strip() for l in comment.splitlines() if l.strip("* ").strip()]
            if lines:
                description = lines[0]
                detail = lines[1] if len(lines) > 1 else ""

            param_pattern = re.compile(r'@param\s+(\w+)\s+(.*)')
            return_pattern = re.compile(r'@return\s+(.*)')
            for line in lines:
                p_match = param_pattern.match(line)
                if p_match:
                    params.append((p_match.group(1), p_match.group(2)))
                r_match = return_pattern.match(line)
                if r_match:
                    return_desc = r_match.group(1)

        if not params:
            params_list = [p.strip().split()[-1] for p in params_str.split(",") if p.strip()]
            params = [(p, f"参数{p}") for p in params_list]
        if not return_desc:
            return_desc = f"返回{func_name}执行结果"
        a = params_str.replace(',', ',\n    ')
        prototype = f"{return_type} {func_name}(\n    {a}\n)"
        functions.append({
            "name": func_name,
            "prototype": prototype,
            "description": description,
            "detail": detail,
            "params": params,
            "return": return_desc,
            "source": os.path.basename(file_path)
        })
    return functions, structs, enums

# ---------------------------------------------------------------------
# 遍历所有头文件
# ---------------------------------------------------------------------
def parse_all_headers(folder):
    all_funcs = []
    all_structs = []
    all_enums = []
    for root, _, files in os.walk(folder):
        for filename in files:
            if filename.endswith(".h"):
                path = os.path.join(root, filename)
                funcs, structs, enums = parse_single_header(path)
                all_funcs.extend(funcs)
                all_structs.extend(structs)
                all_enums.extend(enums)
                print(f"✅ {filename} → 函数:{len(funcs)} 结构体:{len(structs)} 枚举:{len(enums)}")
    return all_funcs, all_structs, all_enums

# ---------------------------------------------------------------------
# 生成 HTML（函数 + 结构体 + 枚举，代码保留换行缩进）
# ---------------------------------------------------------------------
def generate_html_pages(functions, structs, enums, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    # 函数页面
    for func in functions:
        html = f"""<html>
<head>
    <meta charset="gb2312">
    <title>{func['name']}()</title>
    <style>
        body {{ font-family: Microsoft YaHei; margin:20px; font-size:14px; }}
        .func {{ font-size:16px; font-weight:bold; margin-bottom:8px; }}
        .proto {{ background:#f4f4f4; padding:10px; border-left:4px solid #36c; font-family: Consolas; white-space:pre; }}
        .section {{ margin-top:16px; }}
        h4 {{ margin-bottom:6px; font-size:14px; }}
    </style>
</head>
<body>
    <div class="func">{func['name']}()</div>
    <div class="proto">{func['prototype']}</div>
    <div class="section">
        <h4>功能：{func['description']}</h4>
        <p>{func['detail']}</p>
    </div>
    <div class="section">
        <h4>来源文件：{func['source']}</h4>
    </div>
    <div class="section">
        <h4>参数</h4>
        <ul>{"".join(f"<li><b>{p[0]}</b>：{p[1]}</li>" for p in func['params'])}</ul>
    </div>
    <div class="section">
        <h4>返回值</h4>
        <p>{func['return']}</p>
    </div>
</body>
</html>"""
        with open(os.path.join(output_dir, f"{func['name']}.html"), "w", encoding="gb2312", errors="replace") as f:
            f.write(html)

    # 结构体页面（保留源代码换行、缩进）
    for s in structs:
        if not s['name']:
            continue
        html = f"""<html>
<head>
    <meta charset="gb2312">
    <title>struct {s['name']}</title>
    <style>
        body {{ font-family: Microsoft YaHei; margin:20px; font-size:14px; }}
        .title {{ font-size:16px; font-weight:bold; color:#0066cc; margin-bottom:10px; }}
        .code {{ background:#f8f8f8; padding:12px; font-family: Consolas; border-left:4px solid #0066cc; white-space:pre; text-align:left; }}
    </style>
</head>
<body>
    <div class="title">结构体：{s['name']}</div>
    <div class="code">{s['full_code']}</div>
</body>
</html>"""
        with open(os.path.join(output_dir, f"struct_{s['name']}.html"), "w", encoding="gb2312", errors="replace") as f:
            f.write(html)

    # 枚举页面（保留源代码换行、缩进）
    for e in enums:
        if not e['name']:
            continue
        html = f"""<html>
<head>
    <meta charset="gb2312">
    <title>enum {e['name']}</title>
    <style>
        body {{ font-family: Microsoft YaHei; margin:20px; font-size:14px; }}
        .title {{ font-size:16px; font-weight:bold; color:#069; margin-bottom:10px; }}
        .code {{ background:#f8f8f8; padding:12px; font-family: Consolas; border-left:4px solid #069; white-space:pre; text-align:left; }}
    </style>
</head>
<body>
    <div class="title">枚举：{e['name']}</div>
    <div class="code">{e['full_code']}</div>
</body>
</html>"""
        with open(os.path.join(output_dir, f"enum_{e['name']}.html"), "w", encoding="gb2312", errors="replace") as f:
            f.write(html)

# ---------------------------------------------------------------------
# 生成目录（可展开/折叠）
# ---------------------------------------------------------------------
def generate_hhc(functions, structs, enums, output_dir):
    hhc = """<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">
<HTML><HEAD>
<meta name="GENERATOR" content="Microsoft HTML Help Workshop 4.1">
</HEAD><BODY>
<OBJECT type="text/site properties">
    <param name="Window Styles" value="0x800027">
    <param name="Use FTS" value="Yes">
    <param name="FTS Index" value="Yes">
</OBJECT>

<UL>
    <LI><OBJECT type="text/sitemap"><param name="Name" value="函数列表"></OBJECT>
    <UL>
"""
    for func in functions:
        hhc += f"""        <LI><OBJECT type="text/sitemap">
            <param name="Name" value="{func['name']}()">
            <param name="Local" value="{func['name']}.html">
        </OBJECT>
"""
    hhc += """    </UL></LI>

    <LI><OBJECT type="text/sitemap"><param name="Name" value="结构体列表"></OBJECT>
    <UL>
"""
    for s in structs:
        if s['name']:
            hhc += f"""        <LI><OBJECT type="text/sitemap">
            <param name="Name" value="struct {s['name']}">
            <param name="Local" value="struct_{s['name']}.html">
        </OBJECT>
"""
    hhc += """    </UL></LI>

    <LI><OBJECT type="text/sitemap"><param name="Name" value="枚举列表"></OBJECT>
    <UL>
"""
    for e in enums:
        if e['name']:
            hhc += f"""        <LI><OBJECT type="text/sitemap">
            <param name="Name" value="enum {e['name']}">
            <param name="Local" value="enum_{e['name']}.html">
        </OBJECT>
"""
    hhc += """    </UL></LI>
</UL>

</BODY></HTML>"""
    with open(os.path.join(output_dir, "index.hhc"), "w", encoding="gb2312", errors="replace") as f:
        f.write(hhc)

# ---------------------------------------------------------------------
# 生成项目文件
# ---------------------------------------------------------------------
def generate_hhp(functions, structs, enums, output_dir):
    if functions:
        first = functions[0]['name']
    elif structs:
        first = f"struct_{structs[0]['name']}"
    elif enums:
        first = f"enum_{enums[0]['name']}"
    else:
        first = "index"

    hhp = f"""[OPTIONS]
Compatibility=1.1 or later
Compiled file={CHM_NAME}
Contents file=index.hhc
Default topic={first}.html
Language=0x804
Display compile progress=No
Title=C语言接口帮助文档
Full-text search=Yes

[FILES]
"""
    for func in functions:
        hhp += f"{func['name']}.html\n"
    for s in structs:
        if s['name']:
            hhp += f"struct_{s['name']}.html\n"
    for e in enums:
        if e['name']:
            hhp += f"enum_{e['name']}.html\n"

    with open(os.path.join(output_dir, "project.hhp"), "w", encoding="gb2312", errors="replace") as f:
        f.write(hhp)

# ---------------------------------------------------------------------
# 编译 CHM
# ---------------------------------------------------------------------
def compile_chm():
    print("\n🚀 开始编译 CHM...")
    hhp_path = os.path.join(OUTPUT_DIR, "project.hhp")
    res = subprocess.run([HHC_PATH, hhp_path], cwd=OUTPUT_DIR)
    if res.returncode == 0:
        print(f"✅ 编译成功！文件：{os.path.abspath(os.path.join(OUTPUT_DIR, CHM_NAME))}")
    else:
        print("❌ 编译失败！")

# ---------------------------------------------------------------------
# 主程序
# ---------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("  多C头文件 → CHM 自动生成工具（函数+结构体+枚举+搜索）")
    print("=" * 60)

    all_funcs, all_structs, all_enums = parse_all_headers(HEADER_FOLDER)
    if not all_funcs and not all_structs and not all_enums:
        print("\n⚠️ 未找到任何内容")
        exit()

    print(f"\n📦 总计：函数 {len(all_funcs)} 个，结构体 {len(all_structs)} 个，枚举 {len(all_enums)} 个")

    generate_html_pages(all_funcs, all_structs, all_enums, OUTPUT_DIR)
    generate_hhc(all_funcs, all_structs, all_enums, OUTPUT_DIR)
    generate_hhp(all_funcs, all_structs, all_enums, OUTPUT_DIR)

    compile_chm()
