"""天气查询 + 旅游地点推荐

流程：requests 查天气 -> tavily 搜索旅游资料 -> DeepSeek(openai 兼容) 生成建议
密钥从 .env 读取（已被 git 忽略，勿硬编码到代码里）。
"""

import os
import sys

import requests
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")


def check_keys():
    if not DEEPSEEK_API_KEY:
        print("[错误] 未配置 DEEPSEEK_API_KEY，请在 .env 中填入")
        sys.exit(1)
    if not TAVILY_API_KEY:
        print("[错误] 未配置 TAVILY_API_KEY，请在 .env 中填入")
        sys.exit(1)


def get_weather(city):
    """Open-Meteo 免费接口，无需 key：城市名 -> 经纬度 -> 当前天气"""
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "zh"},
        timeout=10,
    ).json()
    if not geo.get("results"):
        return f"未找到城市「{city}」"
    loc = geo["results"][0]
    wx = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "current_weather": True,
            "timezone": "auto",
        },
        timeout=10,
    ).json()["current_weather"]
    name = loc.get("name", city)
    return (
        f"{name}：温度 {wx['temperature']}°C，"
        f"天气代码 {wx['weathercode']}，风速 {wx['windspeed']} km/h"
    )


def search_travel(city):
    """用 Tavily 搜索该城市的旅游景点资料"""
    resp = TavilyClient(api_key=TAVILY_API_KEY).search(
        query=f"{city} 旅游景点推荐 必去",
        search_depth="basic",
        max_results=5,
    )
    results = resp.get("results", []) if isinstance(resp, dict) else getattr(resp, "results", [])
    return "\n".join(f"- {r.get('title', '')}: {r.get('content', '')[:100]}" for r in results)


def recommend(city, weather_text, travel_info):
    """让 DeepSeek 结合天气和搜索资料给出旅游建议"""
    prompt = f"""你是资深旅游规划师。用户想了解「{city}」的天气并得到旅游推荐。

当前天气：{weather_text}

网上搜索到的景点资料：
{travel_info or "（无）"}

请结合天气给出：1) 是否适合旅游；2) 推荐 3-5 个地点及理由；3) 出行建议（穿衣、时间）。用中文回答，简洁实用。"""
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    reply = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return reply.choices[0].message.content


def main():
    if hasattr(sys.stdout, "reconfigure"):  # Windows 控制台中文乱码修复
        sys.stdout.reconfigure(encoding="utf-8")
    check_keys()
    city = input("请输入城市名（如：杭州）：").strip()
    if not city:
        print("城市名不能为空")
        return

    print(f"\n[1/3] 查询「{city}」天气...")
    weather_text = get_weather(city)
    print("天气：", weather_text)

    print("\n[2/3] 搜索旅游资料...")
    travel_info = search_travel(city)
    print(travel_info or "（Tavily 未返回结果）")

    print("\n[3/3] DeepSeek 生成旅游建议...")
    print("\n===== 旅游建议 =====\n")
    print(recommend(city, weather_text, travel_info))


if __name__ == "__main__":
    main()
