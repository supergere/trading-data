"""
Daily Trading Quotes Fetcher
抓 Yahoo Finance API → 寫 JSON → git push
"""

import requests
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

# === 要監控的標的 ===
TW_STOCKS = {
    "2330.TW": "台積電",
    "2317.TW": "鴻海",
    "2308.TW": "台達電",
    "2376.TW": "技嘉",
    "2383.TW": "台光電",
    "6274.TWO": "台燿",
    "2395.TW": "研華",
    "2467.TW": "志聖",
    "3363.TWO": "上詮",
    "8996.TW": "高力",
    "5536.TWO": "聖暉",
    "3081.TWO": "聯亞",
    "2454.TW": "聯發科",
}

US_STOCKS = ["CEG", "GEV", "MU", "MSFT", "NVDA", "TSLA", "GOOGL", "AMD", "BE", "LITE", "INTC"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def fetch_quote(symbol):
    """抓單一標的最新收盤 + 漲跌幅"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        result = data["chart"]["result"][0]
        closes = result["indicators"]["quote"][0]["close"]
        # 過濾掉 None
        valid_closes = [c for c in closes if c is not None]
        if len(valid_closes) < 2:
            return None
        latest = valid_closes[-1]
        prev = valid_closes[-2]
        chg_pct = (latest - prev) / prev * 100
        return {"close": round(latest, 2), "chg_pct": round(chg_pct, 2)}
    except Exception as e:
        print(f"  ❌ {symbol}: {e}")
        return None

def main():
    today = datetime.now().strftime("%Y%m%d")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    output = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "updated_at": now_str,
        "tw": {},
        "us": {}
    }
    
    print(f"=== 抓 {today} 報價 ===\n")
    print("🇹🇼 台股:")
    tw_ok = 0
    for symbol, name in TW_STOCKS.items():
        code = symbol.split(".")[0]
        q = fetch_quote(symbol)
        if q:
            output["tw"][code] = {"name": name, **q}
            print(f"  ✅ {code} {name}: {q['close']} ({q['chg_pct']:+.2f}%)")
            tw_ok += 1
    
    print(f"\n🇺🇸 美股:")
    us_ok = 0
    for symbol in US_STOCKS:
        q = fetch_quote(symbol)
        if q:
            output["us"][symbol] = q
            print(f"  ✅ {symbol}: {q['close']} ({q['chg_pct']:+.2f}%)")
            us_ok += 1
    
    print(f"\n✅ 共抓 {tw_ok}/{len(TW_STOCKS)} 檔台股, {us_ok}/{len(US_STOCKS)} 檔美股")
    
    # 寫兩個 JSON
    script_dir = Path(__file__).parent
    daily_dir = script_dir / "daily_closing"
    daily_dir.mkdir(exist_ok=True)
    
    dated_file = daily_dir / f"{today}.json"
    latest_file = daily_dir / "latest.json"
    
    with open(dated_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 寫入: {dated_file.name}, latest.json")
    
    # Git push
    print(f"\n🚀 推到 GitHub...")
    try:
        os.chdir(script_dir)
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"Update {today}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("✅ 推送成功!")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Git 操作有問題: {e}")
        print("   (可能是沒變化或網路問題,看上面訊息)")

if __name__ == "__main__":
    main()