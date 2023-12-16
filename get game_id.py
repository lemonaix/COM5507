import re
import pandas as pd
from bs4 import BeautifulSoup

# 指定HTML文件的路径
file_path = 'C:\\Users\\A\\Desktop\\test.html'

# 直接使用文件句柄创建BeautifulSoup对象
with open(file_path, 'r', encoding='utf-8') as file:
    soup = BeautifulSoup(file, 'html.parser')

# 查找所有包含data-appid的<tr>标签
appid_tags = soup.find_all('tr', class_='app', attrs={'data-appid': True})

# 提取data-appid的值
appid_values = [tag['data-appid'] for tag in appid_tags]

# 创建一个DataFrame
appid_df = pd.DataFrame({'data-appid': appid_values})

# 将DataFrame保存为Excel文件
output_excel_path = 'C:\\Users\\A\\Desktop\\output_appid_data.xlsx'  # 您可以根据需要修改这个路径
appid_df.to_excel(output_excel_path, index=False)