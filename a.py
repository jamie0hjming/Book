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
