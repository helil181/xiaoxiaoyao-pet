import json
import os
import threading
import time
import requests
from local_cache import get_unsynced_messages, mark_synced, save_message, get_all_messages


def _load_supabase_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("supabase_url", ""), config.get("supabase_anon_key", "")
    except Exception:
        return "", ""


SUPABASE_URL, SUPABASE_ANON_KEY = _load_supabase_config()
REST_URL = (SUPABASE_URL + "/rest/v1/messages") if SUPABASE_URL else ""

CLOUD_ENABLED = False

def _headers():
    return {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def try_init_supabase():
    global CLOUD_ENABLED
    try:
        resp = requests.get(
            REST_URL + "?select=id&limit=1",
            headers=_headers(),
            timeout=10
        )
        if resp.status_code in (200, 206):
            CLOUD_ENABLED = True
            return True
    except:
        pass
    CLOUD_ENABLED = False
    return False

def sync_to_cloud():
    if not CLOUD_ENABLED:
        return
    try:
        unsynced = get_unsynced_messages()
        for msg in unsynced:
            data = {
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["timestamp"]
            }
            resp = requests.post(
                REST_URL,
                headers=_headers(),
                json=data,
                timeout=10
            )
            if resp.status_code in (200, 201):
                mark_synced(msg["id"])
    except Exception:
        pass

def trigger_sync():
    if not CLOUD_ENABLED:
        try_init_supabase()
    threading.Thread(target=sync_to_cloud, daemon=True).start()

def start_sync_loop():
    def loop():
        global CLOUD_ENABLED
        while True:
            if not CLOUD_ENABLED:
                try_init_supabase()
            if CLOUD_ENABLED:
                sync_to_cloud()
            time.sleep(60)
    t = threading.Thread(target=loop, daemon=True)
    t.start()

try_init_supabase()
start_sync_loop()