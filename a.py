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
