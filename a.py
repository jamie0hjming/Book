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
def parse_and_expand(s):
    """
    解析类似：
      '0..2'
      '0..3,reserved:4'
    输出所有段：正常段 / reserved 段
    """
    parts = s.split(',')
    range_part = parts[0]

    # 解析正常段长度
    start, end = map(int, range_part.split('..'))
    normal_len = end - start + 1

    # 解析 reserved 长度
    reserved_len = 0
    for p in parts[1:]:
        if p.startswith('reserved:'):
            reserved_len = int(p.split(':')[1])

    # 从 start 开始，无限循环：正常 → reserved → 正常 → reserved...
    current = start
    while True:
        # 输出正常段
        yield 'normal', current, current + normal_len - 1
        current += normal_len

        if reserved_len <= 0:
            break

        # 输出 reserved 段
        yield 'reserved', current, current + reserved_len - 1
        current += reserved_len


# ===================== 示例使用 =====================
groups = [
    '0..2',
    '0..3,reserved:4',
]

for i, g in enumerate(groups, 1):
    print(f"第{i}组：{g}")
    print("分段范围：")
    gen = parse_and_expand(g)
    # 这里取前10段演示，你想要多少段就改数字
    for _ in range(10):
        try:
            typ, s, e = next(gen)
            print(f"  {typ:8s} {s}..{e}")
        except StopIteration:
            break
    print()
