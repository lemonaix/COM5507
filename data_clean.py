import pandas as pd
import re
from datetime import datetime
#特殊字符转换和移除
def convert_to_number(value):
    if isinstance(value, str):
        # 移除 '$' 和 'h'
        value = value.replace('$', '').replace('h', '').replace('%', '')

        # 检查是否含有 'm' 或 'k' 并转换为数字
        if 'm' in value.lower():
            num = float(value.lower().replace('m', '')) * 1_000_000
        elif 'k' in value.lower():
            num = float(value.lower().replace('k', '')) * 1_000
        else:
            # 如果不包含 'm' 或 'k'，尝试直接转换为浮点数
            try:
                num = float(value)
            except ValueError:
                # 如果转换失败，保持原样
                return value
        return int(num)
    return value

# 读取Excel文件
df = pd.read_excel('C:\\Users\\A\\Desktop\\steam python\\game_id.xlsx')

# 要清洗的列
columns_to_clean = ['positive_review_percentage', 'Revenue Amount', 'Players Total', 'Average Playtime', 'Average Daily Concurrent Players', 'Followers','Owners']

# 评价行清理
for col in columns_to_clean:
    df[col] = df[col].apply(convert_to_number)

def filter_rate(value):
    allowed_values = ['Overwhelmingly Positive', 'Very Positive', 'Mostly Positive','Positive', 'Mixed', 
    'Negative','Mostly Negative', 'Very Negative','Overwhelmingly Negative']

    # 确保输入是字符串
    if not isinstance(value, str):
        value = str(value)

    if value in allowed_values:
        return value, None  # 返回评价和None
    else:
        # 尝试从字符串中提取数字
        numbers = re.findall(r'\d+', value)
        if numbers:
            return None, numbers[0]  # 清除原值并返回找到的数字
        else:
            return None, None  # 清除原值并返回None

# 应用 filter_rate 函数，并根据条件更新列
df['review_rating'], temp_total_reviews = zip(*df['review_rating'].apply(filter_rate))
df['total_reviews'] = df.apply(lambda row: temp_total_reviews[row.name] if pd.isna(row['total_reviews']) else row['total_reviews'], axis=1)

# 日期解析函数
def parse_date(date_str):
    # 确保 date_str 是一个字符串
    if not isinstance(date_str, str):
        return None, None
    try:
        # 解析日期
        date_obj = datetime.strptime(date_str, '%b %d, %Y')
        # 生成数字日期 YYYYMMDD
        num_date = date_obj.strftime('%Y%m%d')
        # 提取月份
        month = date_obj.month
        return num_date, month
    except ValueError:
        # 如果日期格式不正确，返回空值或者自定义的占位符
        return None, None

df['numeric_date'], df['month'] = zip(*df['release_date'].apply(parse_date))

# 删除 Revenue Range 列
df = df.drop(columns=['Revenue Range'])

# 删除 release_date 列
df = df.drop(columns=['release_date']) 

# 删除 game_name 列中无数据的行
df = df.dropna(subset=['game_name'])

# 删除12月的内容
df = df[df['month'] != 12]

# 保存清洗后的数据到新的Excel文件
df.to_excel('C:\\Users\\A\\Desktop\\steam python\\data_clean.xlsx', index=False)

