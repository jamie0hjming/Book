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


def parse_part(s):
    """解析一段：支持 0..3 或 0..4,reserved:2"""
    parts = s.split(',')
    # 正常序号
    s_range = parts[0]
    start, end = map(int, s_range.split('..'))
    seq = list(range(start, end + 1))
    # 解析 reserved
    for p in parts[1:]:
        if p.startswith('reserved:'):
            n = int(p.split(':')[1])
            seq += ['reserved'] * n
    return seq


def flatten_indices(groups):
    """
    多层嵌套遍历，按顺序生成全局 index，只保留非 reserved
    groups: 元组列表，如 ('0..3','0..4,reserved:2')
    返回：所有有效序号
    """
    seqs = [parse_part(g) for g in groups]

    valid = []
    idx = 0

    # 递归 N 层循环
    def dfs(level, current):
        nonlocal idx
        if level == len(seqs):
            # 所有维度都不是 reserved 才保留
            if all(v != 'reserved' for v in current):
                valid.append(idx)
            idx += 1
            return
        for v in seqs[level]:
            current.append(v)
            dfs(level + 1, current)
            current.pop()

    dfs(0, [])
    return valid


def to_ranges(seq):
    """把序号列表转成 0-4,7-11 格式"""
    if not seq:
        return []
    ranges = []
    begin = prev = seq[0]
    for x in seq[1:]:
        if x != prev + 1:
            ranges.append(f"{begin}-{prev}" if begin != prev else f"{begin}")
            begin = x
        prev = x
    ranges.append(f"{begin}-{prev}" if begin != prev else f"{begin}")
    return ", ".join(ranges)


# ======================
# 这里随便改，支持 2/3/4 段
# ======================
if __name__ == '__main__':
    # 示例 1：你原来的 2 段
    group = ('0..3', '0..4,reserved:2')

    # 示例 2：3段（随便测试）
    # group = ('0..1', '0..1,reserved:1', '0..2')

    # 示例 3：4段
    # group = ('0..1', '0..1', '0..1,reserved:1', '0..1')

    valid = flatten_indices(group)
    print("有效区间:", to_ranges(valid))
    print("有效总数:", len(valid))
11111111111

def parse_part(s):
    """解析一段：支持 0..3 或 0..4,reserved:2"""
    parts = s.split(',')
    # 正常序号
    s_range = parts[0]
    start, end = map(int, s_range.split('..'))
    seq = list(range(start, end + 1))
    # 解析 reserved
    for p in parts[1:]:
        if p.startswith('reserved:'):
            n = int(p.split(':')[1])
            seq += ['reserved'] * n
    return seq


def flatten_indices(groups):
    """
    多层嵌套遍历，按顺序生成全局 index，只保留非 reserved
    groups: 元组列表，如 ('0..3','0..4,reserved:2')
    返回：所有有效序号
    """
    seqs = [parse_part(g) for g in groups]

    valid = []
    idx = 0

    # 递归 N 层循环
    def dfs(level, current):
        nonlocal idx
        if level == len(seqs):
            # 所有维度都不是 reserved 才保留
            if all(v != 'reserved' for v in current):
                valid.append(idx)
            idx += 1
            return
        for v in seqs[level]:
            current.append(v)
            dfs(level + 1, current)
            current.pop()

    dfs(0, [])
    return valid


def to_ranges(seq):
    """把序号列表转成 0-4,7-11 格式"""
    if not seq:
        return []
    ranges = []
    begin = prev = seq[0]
    for x in seq[1:]:
        if x != prev + 1:
            ranges.append(f"{begin}-{prev}" if begin != prev else f"{begin}")
            begin = x
        prev = x
    ranges.append(f"{begin}-{prev}" if begin != prev else f"{begin}")
    return ", ".join(ranges)


# ======================
# 这里随便改，支持 2/3/4 段
# ======================
if __name__ == '__main__':
    # 示例 1：你原来的 2 段
    group = ('0..3', '0..4,reserved:2')

    # 示例 2：3段（随便测试）
    # group = ('0..1', '0..1,reserved:1', '0..2')

    # 示例 3：4段
    # group = ('0..1', '0..1', '0..1,reserved:1', '0..1')

    valid = flatten_indices(group)
    print("有效区间:", to_ranges(valid))
    print("有效总数:", len(valid))
