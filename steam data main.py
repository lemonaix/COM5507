import requests
import re
import sqlite3
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

#年龄验证解决方法
def selenium_age_verification(url):
    edge_options = EdgeOptions()
    edge_options.add_argument("--headless")
    edge_options.add_argument("--window-size=1920,1080")
    with webdriver.Edge(options=edge_options) as browser:
        browser.get(url)
        wait = WebDriverWait(browser, 5)
        
        try:
            # 等待年龄验证元素加载
            wait.until(EC.presence_of_element_located((By.ID, "ageDay")))
            Select(browser.find_element(By.ID, "ageDay")).select_by_value("21")

            wait.until(EC.presence_of_element_located((By.ID, "ageMonth")))
            Select(browser.find_element(By.ID, "ageMonth")).select_by_index(2)

            wait.until(EC.presence_of_element_located((By.ID, "ageYear")))
            Select(browser.find_element(By.ID, "ageYear")).select_by_visible_text("2001")

            wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btnv6_blue_hoverfade")))
            browser.find_element(By.CLASS_NAME, "btnv6_blue_hoverfade").click()

            # 确认页面已经跳转
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "apphub_AppName")))

        except TimeoutException:
            print("页面加载超时或元素未找到")
            return None
        
        # 获取页面源代码
        browser.get(url)  # 重新访问详情页
        browser.implicitly_wait(2)
        return browser.page_source.encode('utf-8').decode()
    
# 从 Steam 网站获取数据
def get_data_from_steam(session, game_id):
    url = f'https://store.steampowered.com/app/{game_id}/'
    response = session.get(url)
    
    # 查看响应状态
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.content, 'html.parser')
    price_tag = soup.find('meta', itemprop='price')

    if not price_tag:  # 如果缺少价格标签，可能需要处理年龄验证
        data = selenium_age_verification(url)
        if data is None:  # 检查返回值是否为 None
            print(f"无法获取游戏 {game_id} 的页面数据")
            return None
        soup = BeautifulSoup(data, 'html.parser')
    
    # 从steam网站源码提取数据
    # 游戏名称
    name_div = soup.find('div', class_='apphub_AppName')
    game_name= name_div.get_text().strip()

    # 用户tags
    tags_container = soup.find('div', class_='glance_tags_ctn popular_tags_ctn')
    tags = [tag.get_text().strip() for tag in tags_container.find_all('a', class_='app_tag')] if tags_container else []

    # 价格
    price_tag = soup.find('meta', itemprop='price')
    price = price_tag['content'] if price_tag else None

    # 评论
    total_number = None  # 初始化 total_number
    percentage = None
    review_rating = None
    all_reviews_div = soup.find('div', id='appReviewsAll_responsive')
    review_summary = all_reviews_div.find('span', class_='game_review_summary')
    if review_summary:
        review_rating = review_summary.get_text().strip() if review_summary else None
        total_reviews = all_reviews_div.find('span', class_='responsive_reviewdesc_short')
        if total_reviews:
            total_reviews_text = total_reviews.get_text().strip()
            total_reviews_text = total_reviews_text.replace('(', '').replace(')', '').replace('All', '')
            # 提取百分比和评测总数
            if '%' in total_reviews_text:
                percentage, total_number_text = total_reviews_text.split(' of ')
                total_number = total_number_text.split(' ')[0].replace(',', '')
                percentage = percentage.strip()
    
    # 制作公司
    developer_div = soup.find('div', class_='subtitle column', string='Developer:')
    summary1_div = developer_div.find_next_sibling('div', class_='summary column')if developer_div else None
    developer_name = summary1_div.get_text().strip()if summary1_div else None
    # 发行公司
    publisher_div = soup.find('div', class_='subtitle column', string='Publisher:')
    summary2_div = publisher_div.find_next_sibling('div', class_='summary column')if publisher_div else None
    publisher_name = summary2_div.get_text().strip()if summary2_div else None
    # 发行日期
    date_div = soup.find('div', class_='date')
    release_date = date_div.get_text().strip()

    # 测评数量
    curators_div = soup.find('div', class_='no_curators_followed')
    if curators_div:
        curators_text = curators_div.get_text().strip()
        # 使用正则表达式提取数字
        match = re.search(r'(\d+) Curators have reviewed', curators_text)
        if match:
            number_of_curators = match.group(1)
        else:
            number_of_curators = None
    else:
        number_of_curators = None
    steam_data = {
    'game_name': game_name,
    'tags': ', '.join(tags),
    'price': price,
    'review_rating': review_rating,
    'total_reviews': total_number,
    'positive_review_percentage': percentage,
    'developer_name': developer_name,
    'publisher_name': publisher_name,
    'release_date': release_date,
    'number_of_curators': number_of_curators
    }
    return steam_data  # 返回解析出的游戏数据

# 函数：从 Gamalytic 网站获取数据
def get_data_from_gamalytic(session, game_id):
    url = f'https://gamalytic.com/game/{game_id}/'
    headers = {
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        }
    response = session.get(url)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.content, 'lxml')
    
    #从Gamalytic源码提取数据
    # 收入和收入范围
    gross_revenue_label = soup.find('b', string="Gross revenue: ")
    if gross_revenue_label and gross_revenue_label.next_sibling:
        gross_revenue_div = gross_revenue_label.find_next_sibling('div')
        if gross_revenue_div:
            revenue_text = gross_revenue_div.get_text(strip=True)
            parts = revenue_text.split(' ')
            # 提取收入
            revenue_amount = parts[0]
            # 提取收入范围
            revenue_range = ' '.join(parts[1:])
            revenue_range = revenue_range.replace('(', '').replace(')', '')
        else:
            revenue_range = None
            revenue_amount = None
    else:
        revenue_range = None
        revenue_amount = None
    # 玩家数量
    Players_total_label = soup.find('b', string="Players total: ")
    if Players_total_label and Players_total_label.next_sibling:
        Players_total_label = Players_total_label.find_next_sibling('div')if Players_total_label else None
        Players_total_text =Players_total_label.get_text(strip=True)
    else:
        Players_total_text = None
    # 购买玩家数量
    owners_label = soup.find('b', string="Owners: ")
    owners_text = owners_label.find_next_sibling('div').get_text(strip=True) if owners_label and owners_label.next_sibling else None

    # 平均游戏时间
    average_playtime_label = soup.find('b', string="Average playtime: ")
    average_playtime_text = average_playtime_label.find_next_sibling('div').get_text(strip=True) if average_playtime_label and average_playtime_label.next_sibling else None

    # 每日平均同时在线玩家
    average_daily_concurrent_players_label = soup.find('b', string="Average daily concurrent players: ")
    average_daily_concurrent_players_text = average_daily_concurrent_players_label.find_next_sibling('div').get_text(strip=True) if average_daily_concurrent_players_label and average_daily_concurrent_players_label.next_sibling else None

    # 关注者
    followers_label = soup.find('b', string="Followers: ")
    followers_text = followers_label.find_next_sibling('div').get_text(strip=True) if followers_label and followers_label.next_sibling else None

    gamalytic_data = {
        'Revenue Amount': revenue_amount,
        'Revenue Range': revenue_range,
        'Players Total': Players_total_text,
        'Owners': owners_text,
        'Average Playtime': average_playtime_text,
        'Average Daily Concurrent Players': average_daily_concurrent_players_text,
        'Followers': followers_text
    }
    return gamalytic_data  # 返回解析出的游戏数据

# 主程序
# 创建SQLite数据库连接
conn = sqlite3.connect('steam_data.db')

def main():
    excel_file = r'C:\Users\A\Desktop\steam python\test.xlsx'
    column_name = 'game_id'

    try:
        df = pd.read_excel(excel_file, engine='openpyxl')
    except FileNotFoundError:
        print("文件未找到，请检查路径是否正确。")
        return

    collected_data = []
    session = requests.Session()

    for game_id in df[column_name]:
        steam_data = get_data_from_steam(session, game_id) or {}
        gamalytic_data = get_data_from_gamalytic(session, game_id) or {}
        combined_data = {'game_id': game_id, **steam_data, **gamalytic_data}
        collected_data.append(combined_data)

        # 将数据保存到SQLite数据库
        partial_data_df = pd.DataFrame([combined_data])
        partial_data_df.to_sql('steam_reviews', conn, if_exists='append', index=False)

    updated_df = pd.merge(df, pd.DataFrame(collected_data), on='game_id', how='left')
    updated_df.to_excel(excel_file, index=False)

if __name__ == "__main__":
    main()
