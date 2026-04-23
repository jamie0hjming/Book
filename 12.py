import re
import os
import subprocess
from dataclasses import dataclass
from typing import Dict, List

# ================= 配置区 =================
PROJECT_ROOT = "./your_c_project"  # 你的C工程根目录
OUTPUT_HTML_DIR = "./docs_html"    # 中间HTML目录
CHM_OUTPUT_PATH = "./api_docs.chm" # 最终CHM输出路径
# ==========================================

@dataclass
class CApiInfo:
    """API信息数据结构"""
    brief: str = ""
    params: Dict[str, str] = None
    return_desc: str = ""
    func_name: str = ""
    content: str = ""
    file_path: str = ""

# --- 1. C代码解析逻辑 (保持你的原有逻辑) ---
COMMENT_PATTERN = re.compile(r'/\*\*(.*?)\*/\s*(.*?)(?=/\*\*|$)', re.S | re.M)
BRIEF_PATTERN = re.compile(r'@brief\s+(.*?)\n')
PARAM_PATTERN = re.compile(r'@param\s+(\w+)\s+(.*?)\n')
RETURN_PATTERN = re.compile(r'@return\s+(.*?)\n')
FUNC_PATTERN = re.compile(r'(\w+)\s*\(.*?\)\s*;')

def parse_comment_api(block: str) -> CApiInfo:
    comment, code = block
    api = CApiInfo(params={})
    # 解析brief
    brief_match = BRIEF_PATTERN.search(comment)
    api.brief = brief_match.group(1).strip() if brief_match else ""
    # 解析param
    api.params = {name: desc.strip() for name, desc in PARAM_PATTERN.findall(comment)}
    # 解析return
    ret_match = RETURN_PATTERN.search(comment)
    api.return_desc = ret_match.group(1).strip() if ret_match else ""
    # 解析函数名
    func_match = FUNC_PATTERN.search(code)
    api.func_name = func_match.group(1) if func_match else ""
    api.content = code.strip()
    return api

def scan_c_file(file_path: str) -> List[CApiInfo]:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    blocks = COMMENT_PATTERN.findall(text)
    return [parse_comment_api(b) for b in blocks if parse_comment_api(b).func_name]

def scan_project(root_dir: str) -> Dict[str, List[CApiInfo]]:
    """扫描整个工程"""
    all_apis = {}
    for root, _, files in os.walk(root_dir):
        for name in files:
            if name.endswith((".c", ".h")):
                file_full_path = os.path.join(root, name)
                apis = scan_c_file(file_full_path)
                if apis:
                    for api in apis:
                        api.file_path = file_full_path
                    all_apis[file_full_path] = apis
    return all_apis

# --- 2. HTML 生成逻辑 (带目录树) ---
def generate_html_docs(api_data: Dict[str, List[CApiInfo]]):
    """生成带目录树的HTML文档"""
    os.makedirs(OUTPUT_HTML_DIR, exist_ok=True)
    # 2.1 生成索引页 (包含文件目录树)
    index_content = [
        "<!DOCTYPE html>",
        "<html>",
        "<head><meta charset='utf-8'><title>C语言API文档</title></head>",
        "<body>",
        "<h1>C语言API文档索引</h1>",
        "<ul>"
    ]
    # 2.2 为每个文件生成详情页
    for file_path, apis in api_data.items():
        # 相对路径，用于在CHM中引用
        rel_file = os.path.relpath(file_path, PROJECT_ROOT)
        html_filename = f"{rel_file.replace(os.sep, '_')}.html"
        file_path_in_html = os.path.join(OUTPUT_HTML_DIR, html_filename)
        
        # 生成单个文件的详情页
        file_content = [
            "<!DOCTYPE html>",
            "<html>",
            f"<head><meta charset='utf-8'><title>{rel_file}</title></head>",
            "<body>",
            f"<h1>文件: {rel_file}</h1>",
            f"<a href='index.html'>返回首页</a>",
            "<hr>"
        ]
        for api in apis:
            file_content.append(f"<h2>函数: {api.func_name}</h2>")
            file_content.append(f"<p><b>功能:</b> {api.brief}</p>")
            if api.params:
                file_content.append("<p><b>参数:</b></p><ul>")
                for name, desc in api.params.items():
                    file_content.append(f"<li><i>{name}</i>: {desc}</li>")
                file_content.append("</ul>")
            if api.return_desc:
                file_content.append(f"<p><b>返回值:</b> {api.return_desc}</p>")
            file_content.append(f"<p><b>代码:</b><pre>{api.content}</pre></p>")
            file_content.append("<hr>")
        
        file_content.extend(["</body>", "</html>"])
        with open(file_path_in_html, "w", encoding="utf-8") as f:
            f.write("\n".join(file_content))
        
        # 在索引页添加链接
        index_content.append(f"<li><a href='{html_filename}'>{rel_file}</a> ({len(apis)} 个API)</li>")

    # 完成索引页
    index_content.extend([
        "</ul>",
        "</body>",
        "</html>"
    ])
    with open(os.path.join(OUTPUT_HTML_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(index_content))
    print(f"✅ HTML文档已生成到: {OUTPUT_HTML_DIR}")

# --- 3. CHM 打包逻辑 ---
def generate_chm():
    """
    使用Windows自带的hhc.exe工具生成CHM。
    需要安装HTML Help Workshop (微软免费工具)。
    下载地址: https://learn.microsoft.com/en-us/previous-versions/windows/desktop/htmlhelp/downloading-the-html-help-workshop
    """
    # 3.1 生成项目文件 (.hhp)
    hhp_content = [
        "[OPTIONS]",
        "Compatibility=1.1 or later",
        f"Compiled file={CHM_OUTPUT_PATH}",
        "Contents file=index.hhc",
        "Default Window=Main",
        "Default topic=index.html",
        "Title=C语言API参考手册",
        "Index file=index.hhk",
        "",
        "[WINDOWS]",
        "Main=index.html,index.hhc,index.hhk,,,,,,,,,,,,,,,,,",
        "",
        "[FILES]",
        # 这里需要列出所有HTML文件，简单起见我们用通配符，实际项目建议精确列出
        "*.html"
    ]
    
    hhp_path = os.path.join(OUTPUT_HTML_DIR, "docs.hhp")
    with open(hhp_path, "w", encoding="utf-8") as f:
        f.write("\n".join(hhp_content))
    
    # 3.2 生成目录文件 (.hhc) - 简化版
    hhc_content = [
        "<!DOCTYPE HTML PUBLIC \"-//IETF//DTD HTML//EN\">",
        "<html>",
        "<head>",
        "<meta name='GENERATOR' content='Python Script'>",
        "</head>",
        "<body>",
        "<ul>",
        "<li><object type='text/sitemap'>",
        "<param name='Name' value='API文档首页'>",
        "<param name='Local' value='index.html'>",
        "</object></li>"
        # 自动添加文件目录
    ]
    for file_path in os.listdir(OUTPUT_HTML_DIR):
        if file_path.endswith(".html") and file_path != "index.html":
            # 从文件名还原显示名称
            display_name = file_path.replace("_", " ").replace(".html", "")
            hhc_content.append(
                f"<li><object type='text/sitemap'><param name='Name' value='{display_name}'/>"
                f"<param name='Local' value='{file_path}'/></object></li>"
            )

    hhc_content.extend([
        "</ul>",
        "</body>",
        "</html>"
    ])
    hhc_path = os.path.join(OUTPUT_HTML_DIR, "index.hhc")
    with open(hhc_path, "w", encoding="utf-8") as f:
        f.write("\n".join(hhc_content))
    
    # 3.3 调用 hhc.exe 编译
    try:
        subprocess.run(["hhc.exe", hhp_path], check=True, capture_output=True)
        print(f"✅ CHM文件已生成: {CHM_OUTPUT_PATH}")
    except FileNotFoundError:
        print("❌ 未找到 hhc.exe。请安装 'HTML Help Workshop' 并将其添加到系统PATH。")
        print("下载地址: https://learn.microsoft.com/en-us/previous-versions/windows/desktop/htmlhelp/downloading-the-html-help-workshop")
    except subprocess.CalledProcessError:
        print("❌ CHM编译失败，请检查HTML文件是否损坏。")

# --- 主函数 ---
if __name__ == "__main__":
    print("正在扫描C工程...")
    api_info = scan_project(PROJECT_ROOT)
    print(f"扫描完成，共发现 {len(api_info)} 个文件包含API注释。")
    
    print("正在生成HTML文档...")
    generate_html_docs(api_info)
    
    print("正在打包CHM文件...")
    generate_chm()
