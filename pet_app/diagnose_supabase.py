"""Supabase 连接诊断脚本
在终端里运行: python diagnose_supabase.py
"""
import requests
import json

URL = "https://dygawjubiwvqxpqtaaow.supabase.co/rest/v1/messages"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR5Z2F3anViaXd2cXhwcXRhYW93Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkyMDY2NzMsImV4cCI6MjA5NDc4MjY3M30.MRZR79-iisnTMT7cDt8de3GNncCxaaxbJTnhH0OZQv8"

def hdrs():
    return {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def run():
    print("=" * 50)
    print("Supabase 连接诊断")
    print("=" * 50)
    print(f"REST URL: {URL}")
    print()

    # 1. GET 测试
    print("--- 1. GET 测试 (查询已有数据) ---")
    try:
        r = requests.get(URL + "?select=id&limit=5", headers=hdrs(), timeout=10)
        print(f"    状态码: {r.status_code}")
        print(f"    返回体: {r.text[:300]}")
        if r.status_code == 200:
            print("    ✅ GET 成功")
        elif r.status_code == 401:
            print("    ❌ 认证失败 (anon key 可能有误)")
        elif r.status_code == 404:
            print("    ❌ 表不存在 (table 'messages' 没创建)")
        elif r.status_code == 406:
            print("    ❌ RLS/权限限制")
        else:
            print(f"    ⚠️ 未预期的状态码")
    except requests.exceptions.ConnectionError:
        print("    ❌ 网络连接失败 (dns/代理/防火墙)")
    except Exception as e:
        print(f"    ❌ 异常: {e}")
    print()

    # 2. POST 测试
    print("--- 2. POST 测试 (写入一条测试数据) ---")
    try:
        test_data = {"role": "test", "content": "supabase诊断测试", "timestamp": "2026-05-20T12:00:00"}
        r = requests.post(URL, headers=hdrs(), json=test_data, timeout=10)
        print(f"    状态码: {r.status_code}")
        print(f"    返回体: {r.text[:300]}")
        if r.status_code in (200, 201):
            print("    ✅ POST 成功! 可以去 Supabase 表里查看了")
        elif r.status_code == 401:
            print("    ❌ 认证失败")
        elif r.status_code == 404:
            print("    ❌ 表不存在")
        elif r.status_code == 406:
            print("    ❌ RLS/权限限制")
        else:
            print(f"    ⚠️ 未预期的状态码")
    except Exception as e:
        print(f"    ❌ 异常: {e}")
    print()

    # 3. 本地缓存检查
    print("--- 3. 本地缓存检查 ---")
    try:
        from local_cache import get_unsynced_messages, get_all_messages
        all_msgs = get_all_messages()
        unsynced = get_unsynced_messages()
        print(f"    本地总消息数: {len(all_msgs)}")
        print(f"    未同步消息数: {len(unsynced)}")
        if unsynced:
            print(f"    最后一条未同步: {unsynced[-1]['content'][:50]}...")
    except Exception as e:
        print(f"    读取本地缓存失败: {e}")
    print()

    print("=" * 50)
    print("诊断完成。请把上面的输出截图发给我。")
    print("=" * 50)

if __name__ == "__main__":
    run()