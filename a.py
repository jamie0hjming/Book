def build_combined_list(data, parent_reg_name=None, parent_field_name=None, result=None):
    if result is None:
        result = []

    # 获取当前层的 reg_name
    current_reg_name = data.get('reg_name')

    # 如果存在上一级的 reg_name 和 field_name，组合成列表并添加到结果中
    if parent_reg_name and parent_field_name and current_reg_name:
        combined = [parent_reg_name, parent_field_name, current_reg_name]
        result.append(combined)

    # 处理当前层的 fields
    fields = data.get('fields', [])
    for field in fields:
        field_name = field.get('name')
        sub_regs = field.get('sub_regs', [])

        # 递归处理 sub_regs
        for sub_reg in sub_regs:
            build_combined_list(sub_reg, current_reg_name, field_name, result)

    return result

# 示例数据结构
data = {
    'reg_name': 'root',
    'fields': [
        {
            'name': 'field1',
            'sub_regs': [
                {
                    'reg_name': 'sub_reg1',
                    'fields': [
                        {
                            'name': 'sub_field1',
                            'sub_regs': [
                                {
                                    'reg_name': 'sub_sub_reg1',
                                    'fields': [
                                        {
                                            'name': 'sub_sub_field1',
                                            'sub_regs': [
                                                {
                                                    'reg_name': 'sub_sub_sub_reg1',
                                                    'fields': [
                                                        {
                                                            'name': 'sub_sub_sub_field1',
                                                            'sub_regs': []
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}

# 调用函数生成组合列表
combined_list = build_combined_list(data)
print(combined_list)



def build_combined_list(data, parent_reg_name=None, parent_field_name=None, result=None):
    if result is None:
        result = []

    # 获取当前层的 reg_name
    current_reg_name = data.get('reg_name')

    # 处理当前层的 fields
    fields = data.get('fields', [])
    for field in fields:
        field_name = field.get('name')
        field_desc = field.get('field_desc', '')  # 获取 field_desc，默认为空字符串
        sub_regs = field.get('sub_regs', [])

        # 如果存在上一级的 reg_name 和 field_name，以及当前级的 field_name 和下一级的 reg_name
        if parent_reg_name and parent_field_name and current_reg_name and field_name:
            # 遍历下一级的 sub_regs
            for sub_reg in sub_regs:
                sub_reg_name = sub_reg.get('reg_name')
                if sub_reg_name:
                    # 组合成列表并添加到结果中
                    combined = [
                        parent_reg_name,
                        f"{parent_field_name}:{field.get('field_desc', '')}",  # 上一级的 field_name 和 field_desc
                        current_reg_name,
                        f"{field_name}:{field_desc}",  # 当前级的 field_name 和 field_desc
                        sub_reg_name
                    ]
                    result.append(combined)

        # 递归处理 sub_regs
        for sub_reg in sub_regs:
            build_combined_list(sub_reg, current_reg_name, field_name, result)

    return result

# 示例数据结构
data = {
    'reg_name': 'root',
    'fields': [
        {
            'name': 'field1',
            'field_desc': 'description1',  # 新增 field_desc
            'sub_regs': [
                {
                    'reg_name': 'sub_reg1',
                    'fields': [
                        {
                            'name': 'sub_field1',
                            'field_desc': 'description2',  # 新增 field_desc
                            'sub_regs': [
                                {
                                    'reg_name': 'sub_sub_reg1',
                                    'fields': [
                                        {
                                            'name': 'sub_sub_field1',
                                            'field_desc': 'description3',  # 新增 field_desc
                                            'sub_regs': [
                                                {
                                                    'reg_name': 'sub_sub_sub_reg1',
                                                    'fields': [
                                                        {
                                                            'name': 'sub_sub_sub_field1',
                                                            'field_desc': 'description4',  # 新增 field_desc
                                                            'sub_regs': []
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}

# 调用函数生成组合列表
combined_list = build_combined_list(data)
print(combined_list)



import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog
import csv

# 设置全局字体和颜色
FONT = ("Arial", 12)
BG_COLOR = "#f0f0f0"
BUTTON_COLOR = "#4CAF50"
BUTTON_HOVER_COLOR = "#45a049"

class LoginPage:
    def __init__(self, root):
        self.root = root
        self.root.title("登录页面")
        self.root.geometry("400x300")
        self.root.configure(bg=BG_COLOR)

        # 标题
        self.label_title = tk.Label(root, text="欢迎登录", font=("Arial", 16, "bold"), bg=BG_COLOR)
        self.label_title.pack(pady=20)

        # 用户名输入框
        self.frame_username = tk.Frame(root, bg=BG_COLOR)
        self.frame_username.pack(pady=10)
        self.label_username = tk.Label(self.frame_username, text="用户名:", font=FONT, bg=BG_COLOR)
        self.label_username.pack(side=tk.LEFT, padx=10)
        self.entry_username = tk.Entry(self.frame_username, font=FONT)
        self.entry_username.pack(side=tk.LEFT)

        # 密码输入框
        self.frame_password = tk.Frame(root, bg=BG_COLOR)
        self.frame_password.pack(pady=10)
        self.label_password = tk.Label(self.frame_password, text="密码:", font=FONT, bg=BG_COLOR)
        self.label_password.pack(side=tk.LEFT, padx=10)
        self.entry_password = tk.Entry(self.frame_password, show="*", font=FONT)
        self.entry_password.pack(side=tk.LEFT)

        # 登录按钮
        self.login_button = tk.Button(root, text="登录", font=FONT, bg=BUTTON_COLOR, fg="white",
                                      activebackground=BUTTON_HOVER_COLOR, command=self.login)
        self.login_button.pack(pady=20)

    def login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()

        # 简单的登录验证
        if username == "admin" and password == "password":
            self.root.destroy()
            app = MainApp()
        else:
            messagebox.showerror("错误", "用户名或密码错误")


class MainApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("首页")
        self.root.geometry("400x300")
        self.root.configure(bg=BG_COLOR)

        # 标题
        self.label_title = tk.Label(self.root, text="首页", font=("Arial", 16, "bold"), bg=BG_COLOR)
        self.label_title.pack(pady=20)

        # 功能1按钮
        self.button_page1 = tk.Button(self.root, text="功能1", font=FONT, bg=BUTTON_COLOR, fg="white",
                                     activebackground=BUTTON_HOVER_COLOR, command=self.open_page1)
        self.button_page1.pack(pady=10)

        # 功能2按钮
        self.button_page2 = tk.Button(self.root, text="功能2", font=FONT, bg=BUTTON_COLOR, fg="white",
                                     activebackground=BUTTON_HOVER_COLOR, command=self.open_page2)
        self.button_page2.pack(pady=10)

        self.root.mainloop()

    def open_page1(self):
        self.root.destroy()
        app = FunctionPage1()

    def open_page2(self):
        self.root.destroy()
        app = FunctionPage2()


class FunctionPage1:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("功能页面1")
        self.root.geometry("600x500")
        self.root.configure(bg=BG_COLOR)

        # 标题
        self.label_title = tk.Label(self.root, text="功能页面1", font=("Arial", 16, "bold"), bg=BG_COLOR)
        self.label_title.pack(pady=10)

        # URL 输入框和获取标签按钮
        self.frame_url = tk.Frame(self.root, bg=BG_COLOR)
        self.frame_url.pack(pady=10)
        self.label_url = tk.Label(self.frame_url, text="URL:", font=FONT, bg=BG_COLOR)
        self.label_url.pack(side=tk.LEFT, padx=10)
        self.entry_url = tk.Entry(self.frame_url, font=FONT, width=30)
        self.entry_url.pack(side=tk.LEFT)
        self.button_get_tags = tk.Button(self.frame_url, text="获取标签", font=FONT, bg=BUTTON_COLOR, fg="white",
                                        activebackground=BUTTON_HOVER_COLOR, command=self.get_tags)
        self.button_get_tags.pack(side=tk.LEFT, padx=10)

        # 开始标签下拉框
        self.frame_start_tag = tk.Frame(self.root, bg=BG_COLOR)
        self.frame_start_tag.pack(pady=10)
        self.label_start_tag = tk.Label(self.frame_start_tag, text="开始标签:", font=FONT, bg=BG_COLOR)
        self.label_start_tag.pack(side=tk.LEFT, padx=10)
        self.start_tag_var = tk.StringVar()
        self.combo_start_tag = ttk.Combobox(self.frame_start_tag, textvariable=self.start_tag_var, state="readonly", font=FONT)
        self.combo_start_tag.pack(side=tk.LEFT)

        # 结束标签下拉框
        self.frame_end_tag = tk.Frame(self.root, bg=BG_COLOR)
        self.frame_end_tag.pack(pady=10)
        self.label_end_tag = tk.Label(self.frame_end_tag, text="结束标签:", font=FONT, bg=BG_COLOR)
        self.label_end_tag.pack(side=tk.LEFT, padx=10)
        self.end_tag_var = tk.StringVar()
        self.combo_end_tag = ttk.Combobox(self.frame_end_tag, textvariable=self.end_tag_var, state="readonly", font=FONT)
        self.combo_end_tag.pack(side=tk.LEFT)

        # 获取信息按钮
        self.button_get_info = tk.Button(self.root, text="获取信息", font=FONT, bg=BUTTON_COLOR, fg="white",
                                         activebackground=BUTTON_HOVER_COLOR, command=self.get_info)
        self.button_get_info.pack(pady=10)

        # 表格
        self.tree_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.tree_frame.pack(pady=10)
        self.tree = ttk.Treeview(self.tree_frame, columns=("类型", "名称"), show="headings", height=10)
        self.tree.heading("类型", text="类型")
        self.tree.heading("名称", text="名称")
        self.tree.pack(side=tk.LEFT)

        # 滚动条
        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        # 下载按钮
        self.button_download = tk.Button(self.root, text="下载表格", font=FONT, bg=BUTTON_COLOR, fg="white",
                                         activebackground=BUTTON_HOVER_COLOR, command=self.download_table)
        self.button_download.pack(pady=10)

        # 返回首页按钮
        self.button_back = tk.Button(self.root, text="返回首页", font=FONT, bg=BUTTON_COLOR, fg="white",
                                    activebackground=BUTTON_HOVER_COLOR, command=self.back_to_main)
        self.button_back.pack(side=tk.BOTTOM, pady=20)

        # 预设一些表格数据
        self.preset_data()

        self.root.mainloop()

    def get_tags(self):
        # 模拟获取标签的逻辑
        url = self.entry_url.get()
        if url:
            tags = ["tag1", "tag2", "tag3", "tag4"]  # 假设从后台获取到的标签
            self.combo_start_tag['values'] = tags
            self.combo_end_tag['values'] = tags
        else:
            messagebox.showerror("错误", "请输入URL")

    def get_info(self):
        start_tag = self.start_tag_var.get()
        end_tag = self.end_tag_var.get()
        if start_tag and end_tag:
            # 模拟获取信息并更新表格
            self.update_table(start_tag, end_tag)
        else:
            messagebox.showerror("错误", "请选择开始和结束标签")

    def preset_data(self):
        # 预设一些表格数据
        data = [
            ("类型1", "名称1"),
            ("类型2", "名称2"),
            ("类型3", "名称3"),
        ]
        for item in data:
            self.tree.insert("", tk.END, values=item)

    def update_table(self, start_tag, end_tag):
        # 模拟根据标签获取信息并更新表格
        self.tree.delete(*self.tree.get_children())  # 清空表格
        data = [
            (f"类型-{start_tag}", f"名称-{start_tag}"),
            (f"类型-{end_tag}", f"名称-{end_tag}"),
        ]
        for item in data:
            self.tree.insert("", tk.END, values=item)

    def download_table(self):
        # 下载表格数据为 CSV 文件
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV 文件", "*.csv")])
        if file_path:
            with open(file_path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["类型", "名称"])  # 写入表头
                for row in self.tree.get_children():
                    writer.writerow(self.tree.item(row)["values"])  # 写入每一行数据
            messagebox.showinfo("成功", f"表格已保存到 {file_path}")

    def back_to_main(self):
        self.root.destroy()
        app = MainApp()


class FunctionPage2:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("功能页面2")
        self.root.geometry("400x300")
        self.root.configure(bg=BG_COLOR)

        # 标题
        self.label_title = tk.Label(self.root, text="功能页面2", font=("Arial", 16, "bold"), bg=BG_COLOR)
        self.label_title.pack(pady=50)

        # 返回首页按钮
        self.button_back = tk.Button(self.root, text="返回首页", font=FONT, bg=BUTTON_COLOR, fg="white",
                                    activebackground=BUTTON_HOVER_COLOR, command=self.back_to_main)
        self.button_back.pack(pady=10)

        self.root.mainloop()

    def back_to_main(self):
        self.root.destroy()
        app = MainApp()


if __name__ == "__main__":
    root = tk.Tk()
    app = LoginPage(root)
    root.mainloop()

