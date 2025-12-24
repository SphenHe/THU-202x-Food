import json
import os
import sys
import streamlit as st
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import platform
import subprocess

from utils.analyze_data import (
    analyze_patterns,
    get_costs,
    get_max_cost,
    get_time_bounds,
    get_top_counters,
    get_top_locations,
)
from utils.get_eat_record import get_record
from utils.process_data import process_data
from utils.prompts import get_eat_habbit_prompt
from utils.ask_gpt import ask_gpt

st.set_page_config(
    page_title="2025 华子食堂消费总结",
    page_icon="🍜",
    layout="wide"
)

# Load environment variables
load_dotenv()

# Get TEST_MODE from environment variables
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'

# 添加自定义 CSS 样式
def load_css():
    # Resolve path so it works when packaged with PyInstaller (sys._MEIPASS)
    possible_paths = [
        os.path.join(os.getcwd(), 'utils', 'styles.css'),
        os.path.join(os.path.dirname(__file__), 'utils', 'styles.css'),
    ]
    if getattr(sys, 'frozen', False):
        possible_paths.insert(0, os.path.join(sys._MEIPASS, 'utils', 'styles.css'))

    css_text = None
    for p in possible_paths:
        try:
            with open(p, 'r', encoding='utf-8') as f:
                css_text = f.read()
                break
        except UnicodeDecodeError:
            try:
                with open(p, 'r', encoding='gbk') as f:
                    css_text = f.read()
                    break
            except Exception:
                try:
                    with open(p, 'rb') as f:
                        css_text = f.read().decode('utf-8', errors='replace')
                        break
                except Exception:
                    continue
        except FileNotFoundError:
            continue

    if css_text is None:
        st.warning('无法读取样式文件 `utils/styles.css`，将使用默认样式。')
        return

    st.markdown(f'<style>{css_text}</style>', unsafe_allow_html=True)

def create_stat_card(title, value, location, date, comment, emoji=""):
    return f"""
        <div class='stat-card'>
            <div class='stat-label'>{title} {emoji}</div>
            <div class='stat-value'>{value}</div>
            <div class='stat-label'>地点: {location}</div>
            <div class='stat-label'>{'时间' if ':' in date else '日期'}: {date}</div>
            <div class='stat-label'>{comment}</div>
        </div>
    """

def plot_merchant_spending(df_raw):
    # Group by merchant name and sum the transaction amounts
    merchant_spending = df_raw.groupby('mername')['txamt'].sum().sort_values(ascending=True)
    
    # Set Chinese font based on platform
    system = platform.system()
    if system == 'Darwin':  # macOS
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    elif system == 'Linux':
        # Try to install Noto fonts if not present
        try:
            subprocess.run(['apt-get', 'update'], check=True)
            subprocess.run(['apt-get', 'install', '-y', 'fonts-noto-cjk'], check=True)
        except subprocess.CalledProcessError:
            st.warning("无法安装字体，可能需要管理员权限。图表中文显示可能不正常。")
        except FileNotFoundError:
            st.warning("未找到apt-get命令，请手动安装fonts-noto-cjk包。")
        
        plt.rcParams['font.sans-serif'] = ['Noto Sans CJK JP', 'Noto Sans CJK SC', 'Noto Sans CJK TC', 'SimHei', 'SimSun', 'WenQuanYi Micro Hei', 'FangSong_GB2312', 'KaiTi_GB2312']
    else:  # Windows
        plt.rcParams['font.sans-serif'] = ['SimHei', 'SimSun']
    plt.rcParams['axes.unicode_minus'] = False

    # Create high-resolution figure
    plt.figure(figsize=(12, len(merchant_spending) / 66 * 18), dpi=300)
    
    # Set higher quality settings
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['savefig.dpi'] = 300
    plt.rcParams['figure.figsize'] = [12, len(merchant_spending) / 66 * 18]
    plt.rcParams['figure.autolayout'] = True
    
    # Create horizontal bar plot
    plt.barh(range(len(merchant_spending)), merchant_spending)
    
    # Add value labels on the bars with adjusted font size for high DPI
    for i, value in enumerate(merchant_spending):
        plt.text(value + 0.01 * max(merchant_spending), i, 
                f'¥{value:.2f}', va='center', ha='left', fontsize=6)
    
    # Customize the plot with adjusted font sizes
    plt.yticks(range(len(merchant_spending)), merchant_spending.index, fontsize=8)
    plt.xlabel('消费金额（元）', fontsize=10)
    plt.title('各窗口消费总额', fontsize=12)
    plt.xlim(0, 1.2 * max(merchant_spending))
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    return plt.gcf()

def main():
    load_css()
    st.title("🍜 2025 华子食堂消费总结")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ LLM 设置")
        base_url = st.text_input("Base URL", value=os.getenv("BASE_URL", "https://api.deepseek.com"))
        model = st.text_input("Model", value=os.getenv("MODEL", "deepseek-chat"))
        api_key = st.text_input("API Key", value=os.getenv("API_KEY", ""), type="password")
    
    # 更新欢迎页面文案
    st.markdown("""
    
    👋 这是一个专门为华子吃货们打造的 2025 年度美食档案！
    """)

    # 更新用户输入区域文案
    with st.form("user_input"):
        st.subheader("🔑 请出示你的美食证件")
        idserial = st.text_input("学号")
        servicehall = st.text_input("Cookie中的servicehall", help="如何获取？参考 https://github.com/SphenHe/THU-202x-Food")
        submitted = st.form_submit_button("开启美食档案 🚀")

        if TEST_MODE:
            idserial = "2025012345"
            servicehall = "1234567890"
            submitted = True

        # After the form submission check
        if submitted:
            if not idserial or not servicehall:
                st.error("⚠️ 请填写完整信息！")
                return

            # First spinner for data fetching
            with st.spinner("正在获取数据，请稍候..."):
                try:
                    data = get_record(servicehall, idserial) if not TEST_MODE else json.load(open("log.json", "r", encoding='utf-8'))
                    df_raw, df = process_data(data)
                    username = df['username'].iloc[0]
                    st.success("✅ 数据获取成功")
                except Exception as e:
                    st.error(f"❌ 数据获取失败，���检查学号和Cookie是否正确")
                    return

    if submitted:
        # Create expander after successful data fetch
        with st.expander(f"📊 {username}的美食探险日记", expanded=True):
            # Second spinner for report generation
            with st.spinner("正在生成报告，请稍候..."):
                try:
                    # 1. 消费统计卡片
                    st.subheader("💰 年度资金报告")
                    col1, col2 = st.columns(2)
                    
                    avg_cost, total_cost = get_costs(df)
                    with col1:
                        cups = int(total_cost // 13)
                        st.markdown("""
                            <div class='stat-card card-blue'>
                                <div class='stat-label'>2025 一共吃了</div>
                                <div class='stat-value'>¥{total_cost:.2f}</div>
                                <div class='stat-label'>相当于 {cups} 杯生椰拿铁 🥥</div>
                            </div>
                        """.format(total_cost=total_cost, cups=cups), unsafe_allow_html=True)
                    
                    with col2:
                        cups = float(round(avg_cost / 13, 1))
                        st.markdown("""
                            <div class='stat-card card-green'>
                                <div class='stat-label'>平均每顿饭钱</div>
                                <div class='stat-value'>¥{avg_cost:.2f}</div>
                                <div class='stat-label'>相当于 {cups} 杯生椰拿铁 🥥</div>
                            </div>
                        """.format(avg_cost=avg_cost, cups=cups), unsafe_allow_html=True)

                    # 2. 最常光顾食堂展示
                    st.subheader("🏆 你的主力探店地")
                    top_3_canteens = get_top_locations(df)
                    cols = st.columns(3)  # 创建3列
                    
                    for idx, ((location, visits), col) in enumerate(zip(top_3_canteens.items(), cols), 1):
                        color_class = f"card-{'purple' if idx == 1 else 'orange' if idx == 2 else 'red'}"
                        with col:
                            st.markdown(f"""
                                <div class='stat-card {color_class}'>
                                    <div class='stat-label'>第 {idx} 名</div>
                                    <div class='stat-value'>{location}</div>
                                    <div class='stat-label'>一共吃了 {visits} 顿</div>
                                </div>
                            """, unsafe_allow_html=True)
                    st.markdown("", unsafe_allow_html=True)

                    # 3. 最喜爱的窗口
                    st.subheader("🎯 你的心头好")
                    counter_visits = get_top_counters(df)
                    top_5_counters = counter_visits.head()
                    cols = st.columns(5)
                    
                    for idx, ((counter, visits), col) in enumerate(zip(top_5_counters.items(), cols), 1):
                        with col:
                            st.markdown(f"""
                                <div class='stat-card'>
                                    <div class='stat-label'>第 {idx} 名</div>
                                    <div class='stat-value'>{counter.replace('园_', '')}</div>
                                    <div class='stat-label'>吃了 {visits} 次</div>
                                </div>
                            """, unsafe_allow_html=True)
                    st.markdown("", unsafe_allow_html=True)

                    # 4. 最逆天的记录
                    st.subheader("🤡 最逆天的一餐")
                    earliest, latest = get_time_bounds(df)
                    most_expensive = get_max_cost(df)
                    
                    earliest_prompt = get_eat_habbit_prompt(username, earliest)
                    latest_prompt = get_eat_habbit_prompt(username, latest)
                    most_expensive_prompt = get_eat_habbit_prompt(username, most_expensive)
                    
                    earliest_comment = ask_gpt(earliest_prompt, model=model, api_key=api_key, base_url=base_url)
                    latest_comment = ask_gpt(latest_prompt, model=model, api_key=api_key, base_url=base_url)
                    most_expensive_comment = ask_gpt(most_expensive_prompt, model=model, api_key=api_key, base_url=base_url)

                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(
                            create_stat_card(
                                "清晨觅食冠军", 
                                earliest['txdate'].strftime('%H:%M'),
                                earliest['meraddr'],
                                earliest['txdate'].strftime('%Y-%m-%d'),
                                earliest_comment,
                                "☀️"
                            ),
                            unsafe_allow_html=True
                        )
                    
                    with col2:
                        st.markdown(
                            create_stat_card(
                                "夜宵王者",
                                latest['txdate'].strftime('%H:%M'),
                                latest['meraddr'],
                                latest['txdate'].strftime('%Y-%m-%d'),
                                latest_comment,
                                "🌙"
                            ),
                            unsafe_allow_html=True
                        )

                    with col3:
                        st.markdown(
                            create_stat_card(
                                "土豪餐王",
                                f"¥{most_expensive['txamt']:.2f}",
                                most_expensive['meraddr'],
                                most_expensive['txdate'].strftime('%Y-%m-%d %H:%M'),
                                most_expensive_comment,
                                "💫"
                            ),
                            unsafe_allow_html=True
                        )
                    st.markdown("", unsafe_allow_html=True)

                    # Add this section where you want to display the plot
                    st.subheader("💰 细细细则")
                    fig = plot_merchant_spending(df_raw)
                    st.pyplot(fig)
                    plt.close()

                except Exception as e:
                    st.error(f"❌ 生成报告时出现错误: {str(e)}")
                    return

if __name__ == "__main__":
    main()