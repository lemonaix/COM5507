import re
import pandas as pd
from bs4 import BeautifulSoup

# 指定HTML文件的路径
file_path = 'C:\\Users\\A\\Desktop\\steamdb source coede.html'

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
output_excel_path = 'C:\\Users\\A\\Desktop\\game_id.xlsx'  
appid_df.to_excel(output_excel_path, index=False)
