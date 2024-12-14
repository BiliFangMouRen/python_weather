import json
import os
import requests
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
import logging

# 获取当前时间码
current_time_str = datetime.now().strftime('%Y%m%d%H%M%S')

# 创建日志目录
log_dir = 'log'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 配置日志记录器
log_filename = os.path.join(log_dir, f"{current_time_str}_log.log")
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.info("本应用基于t.weather.sojson.com的天气API")

def load_city_codes(file_path):
    """加载城市代码"""
    logging.info(f"正在加载城市代码文件: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as file:
        city_codes = json.load(file)
    logging.info("城市代码加载成功")
    return city_codes

def get_cache_file_path(city_name, time_str):
    """获取缓存文件路径"""
    cache_dir = 'cache'
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        logging.info(f"缓存目录 {cache_dir} 创建成功")
    return os.path.join(cache_dir, f"{city_name}-{time_str}.json")

def load_local_cache(city_name):
    """加载本地缓存文件"""
    logging.info(f"正在加载本地缓存文件: {city_name}")
    cache_dir = 'cache'
    if not os.path.exists(cache_dir):
        logging.info(f"缓存目录 {cache_dir} 不存在")
        return None

    latest_cache_file = None
    latest_time = datetime.min

    for filename in os.listdir(cache_dir):
        if filename.startswith(city_name + '-') and filename.endswith('.json'):
            time_str = filename[len(city_name) + 1:-5]
            try:
                file_time = datetime.fromisoformat(time_str)
                if file_time > latest_time:
                    latest_time = file_time
                    latest_cache_file = filename
            except ValueError:
                logging.warning(f"文件名解析错误: {filename}")
                continue

    if latest_cache_file:
        file_path = os.path.join(cache_dir, latest_cache_file)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                local_cache = json.load(file)
            logging.info(f"本地缓存文件加载成功: {file_path}")
            cached_time_str = local_cache.get('cached_time')
            if cached_time_str:
                cached_time = datetime.fromisoformat(cached_time_str)
                if datetime.now() - cached_time > timedelta(hours=8):
                    logging.info(f"缓存数据已过期，删除文件: {file_path}")
                    os.remove(file_path)
                    return None
            return local_cache
        except (FileNotFoundError, json.JSONDecodeError):
            logging.error(f"本地缓存文件读取失败: {file_path}")
            pass

    logging.info("没有找到有效的本地缓存文件")
    return None

def save_local_cache(city_name, weather_data):
    """保存缓存数据到本地文件"""
    time_str = datetime.now().isoformat()
    file_path = get_cache_file_path(city_name, time_str)
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(weather_data, file, ensure_ascii=False, indent=4)
    logging.info(f"缓存数据已保存到文件: {file_path}")

def get_weather(city_code):
    """根据城市代码获取天气信息"""
    logging.info(f"正在获取城市代码 {city_code} 的天气信息")
    city_info = next((item for item in city_codes if item['cityCode'] == city_code), None)
    if not city_info:
        messagebox.showerror("Error", "城市信息未找到")
        logging.error(f"城市代码 {city_code} 未找到对应的城市信息")
        return None

    city_name = city_info['cityName']
    local_cache = load_local_cache(city_name)

    if local_cache:
        logging.info(f"使用本地缓存数据: {city_code}")
        return local_cache['weather_data']

    url = f"http://t.weather.sojson.com/api/weather/city/{city_code}"
    response = requests.get(url)
    if response.status_code == 200:
        weather_data = response.json()
        cache_data = {
            'cached_time': datetime.now().isoformat(),
            'weather_data': weather_data
        }
        save_local_cache(city_name, cache_data)
        logging.info(f"成功获取并缓存天气数据: {city_code}")
        return weather_data
    else:
        messagebox.showerror("Error", f"无法获取城市代码 {city_code} 的天气数据")
        logging.error(f"无法获取城市代码 {city_code} 的天气数据，状态码: {response.status_code}")
        return None

def display_weather(event=None):
    """显示天气信息"""
    selected_item = city_code_combobox.get()
    logging.info(f"用户选择的城市: {selected_item}")
    city_code = next((item['cityCode'] for item in city_codes if f"{item['cityName']} - {item['province']}" == selected_item), None)
    if city_code:
        weather_data = get_weather(city_code)
        if weather_data:
            if 'cityInfo' in weather_data and 'city' in weather_data['cityInfo']:
                weather_info = f"城市: {weather_data['cityInfo']['city']}\n"
                weather_info += f"日期: {weather_data['data']['forecast'][0]['date']}\n"
                weather_info += f"温度: {weather_data['data']['wendu']}°C\n"
                weather_info += f"湿度: {weather_data['data']['shidu']}\n"
                weather_info += f"空气质量: {weather_data['data']['quality']}\n"
                weather_info += f"建议: {weather_data['data']['ganmao']}\n"
                weather_info += f"天气: {weather_data['data']['forecast'][0]['type']}\n"
                weather_info += f"风向: {weather_data['data']['forecast'][0]['fx']}\n"
                weather_info += f"风力: {weather_data['data']['forecast'][0]['fl']}\n"
                weather_label.config(text=weather_info)
                logging.info("天气信息已显示")
            else:
                messagebox.showerror("Error", "天气数据格式不正确")
                logging.error("天气数据格式不正确，缺少 'cityInfo' 或 'city' 键")
    else:
        messagebox.showerror("Error", "请选择一个有效的城市")
        logging.error("用户选择了无效的城市")

# 初始化缓存
cache = {}

# 加载城市代码
city_codes = load_city_codes('/Users/fangjiachen/PycharmProjects/weather/city_code/2019-03-13-city_code.json')

# 创建主窗口
root = tk.Tk()
root.title("天气查询")

# 创建下拉列表
city_code_combobox = ttk.Combobox(root, values=[f"{item['cityName']} - {item['province']}" for item in city_codes])
city_code_combobox.pack(pady=5)

# 创建按钮
query_button = tk.Button(root, text="查询天气", command=display_weather)
query_button.pack(pady=10)

# 创建显示天气信息的标签
weather_label = tk.Label(root, text="", justify=tk.LEFT)
weather_label.pack(pady=10)

# 运行主循环
root.mainloop()
