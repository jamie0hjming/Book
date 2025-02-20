import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog
import csv

# 设置全局字体和颜色
FONT = ("Arial", 12)
BG_COLOR = "#f0f0f0"
BUTTON_COLOR = "#4CAF50"
BUTTON_HOVER_COLOR = "#45a049"

# ...（LoginPage 和 MainApp 类的代码保持不变，直接跳到 FunctionPage1 类）

class FunctionPage1:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("功能页面1")
        self.root.geometry("600x500")
        self.root.configure(bg=BG_COLOR)
        self.detail_window = None  # 用于跟踪详情窗口

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

        # 表格容器
        self.table_container = tk.Frame(self.root, bg=BG_COLOR)
        self.table_container.pack(pady=10, fill=tk.BOTH, expand=True)

        # 表格
        self.tree_frame = tk.Frame(self.table_container, bg=BG_COLOR)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(self.tree_frame, columns=("类型", "名称"), show="headings", height=10)
        self.tree.heading("类型", text="类型")
        self.tree.heading("名称", text="名称")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 绑定双击事件
        self.tree.bind("<Double-1>", self.show_detail)

        # 滚动条
        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        # 下载按钮容器
        self.download_frame = tk.Frame(self.table_container, bg=BG_COLOR)
        self.download_frame.pack(pady=10, fill=tk.X)
        self.button_download = tk.Button(self.download_frame, text="下载表格", font=FONT, bg=BUTTON_COLOR, fg="white",
                                         activebackground=BUTTON_HOVER_COLOR, command=self.download_table)
        self.button_download.pack(side=tk.LEFT, padx=10)

        # 返回首页按钮
        self.button_back = tk.Button(self.root, text="返回首页", font=FONT, bg=BUTTON_COLOR, fg="white",
                                    activebackground=BUTTON_HOVER_COLOR, command=self.back_to_main)
        self.button_back.pack(side=tk.BOTTOM, pady=20, padx=20, anchor=tk.SE)

        # 预设数据
        self.preset_data()

        self.root.mainloop()

    # ...（get_tags、get_info、preset_data、update_table、download_table、back_to_main 方法保持不变）

    def show_detail(self, event):
        # 关闭已存在的详情窗口
        if self.detail_window:
            self.detail_window.destroy()

        # 获取选中的行
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("错误", "请先选中一行数据")
            return

        # 获取行数据
        item = self.tree.item(selected_item)
        data = item["values"]

        # 创建详情窗口
        self.detail_window = tk.Toplevel(self.root)
        self.detail_window.title("详情信息")
        self.detail_window.geometry("300x200")
        self.detail_window.configure(bg=BG_COLOR)

        # 显示数据
        frame_detail = tk.Frame(self.detail_window, bg=BG_COLOR)
        frame_detail.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

        # 类型详情
        label_type = tk.Label(frame_detail, text="类型:", font=FONT, bg=BG_COLOR)
        label_type.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        entry_type = tk.Entry(frame_detail, font=FONT, state="readonly")
        entry_type.grid(row=0, column=1, padx=5, pady=5)
        entry_type.config(state="normal")
        entry_type.insert(0, data[0])
        entry_type.config(state="readonly")

        # 名称详情
        label_name = tk.Label(frame_detail, text="名称:", font=FONT, bg=BG_COLOR)
        label_name.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        entry_name = tk.Entry(frame_detail, font=FONT, state="readonly")
        entry_name.grid(row=1, column=1, padx=5, pady=5)
        entry_name.config(state="normal")
        entry_name.insert(0, data[1])
        entry_name.config(state="readonly")

        # 关闭按钮
        button_close = tk.Button(
            self.detail_window,
            text="关闭",
            font=FONT,
            bg=BUTTON_COLOR,
            fg="white",
            activebackground=BUTTON_HOVER_COLOR,
            command=self.detail_window.destroy
        )
        button_close.pack(pady=10)

# ...（FunctionPage2 类和主程序代码保持不变）
