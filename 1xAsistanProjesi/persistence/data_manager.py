# persistence/data_manager.py
import json
import os
import datetime
import getpass
import subprocess

import config # config dosyasındaki sabitlere ve global değişkenlere erişim için

# Simple shell command execution function
def run_shell_command(command):
    """Execute a shell command and return the result."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"

# === YÜKLEME FONKSİYONLARI ===
def load_profile():
    """Kullanıcı profilini yükler veya oluşturur."""
    if os.path.exists(config.PROFILE_FILE):
        with open(config.PROFILE_FILE, "r", encoding="utf-8") as f:
            config.user_profile = json.load(f)
    else:
        config.user_profile = {
            "name": getpass.getuser(),
            "home": os.path.expanduser("~"),
            "created_at": str(datetime.datetime.now())
        }
        save_profile() # Yeni profili hemen kaydet

def load_aliases():
    """Takma adları (aliases) yükler."""
    if os.path.exists(config.ALIASES_FILE):
        with open(config.ALIASES_FILE, "r", encoding="utf-8") as f:
            config.aliases = json.load(f)
    else:
        config.aliases = {}

def load_macros():
    """Makroları yükler."""
    if os.path.exists(config.MACRO_FILE):
        with open(config.MACRO_FILE, "r", encoding="utf-8") as f:
            config.macros = json.load(f)
    else:
        config.macros = {}

def load_history():
    """Sohbet geçmişini yükler."""
    if os.path.exists(config.CHAT_HISTORY_FILE):
        with open(config.CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    role, content = line.strip().split(":", 1)
                    config.chat_history.append({"role": role, "content": content})
                except ValueError: # Hatalı formatlı satırları atla
                    continue
    # Geçmişin boyutu MAX_HISTORY'yi aşarsa kırp
    config.chat_history = config.chat_history[-config.MAX_HISTORY:]


def load_found_programs():
    """Kaydedilmiş kullanıcı programlar listesini yükler."""
    if os.path.exists(config.PROGRAM_LIST_FILE):
        with open(config.PROGRAM_LIST_FILE, "r", encoding="utf-8") as f:
            config.found_programs = json.load(f)
    else:
        config.found_programs = {}

def load_system_programs():
    """Kaydedilmiş sistem programlar listesini yükler."""
    if os.path.exists(config.SYSTEM_PROGRAM_LIST_FILE):
        with open(config.SYSTEM_PROGRAM_LIST_FILE, "r", encoding="utf-8") as f:
            config.system_programs = json.load(f)
    else:
        config.system_programs = {}

def load_all_data():
    """Tüm kalıcı verileri yükler."""
    load_profile()
    load_aliases()
    load_macros()
    load_history()
    load_found_programs()
    load_system_programs()

# === KAYDETME FONKSİYONLARI ===
def save_profile():
    """Kullanıcı profilini kaydeder."""
    with open(config.PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(config.user_profile, f, indent=2, ensure_ascii=False)

def save_aliases():
    """Takma adları (aliases) kaydeder."""
    with open(config.ALIASES_FILE, "w", encoding="utf-8") as f:
        json.dump(config.aliases, f, indent=2, ensure_ascii=False)

def save_macros():
    """Makroları kaydeder."""
    with open(config.MACRO_FILE, "w", encoding="utf-8") as f:
        json.dump(config.macros, f, indent=2, ensure_ascii=False)

def save_history():
    """Sohbet geçmişini kaydeder (append mode)."""
    with open(config.CHAT_HISTORY_FILE, "w", encoding="utf-8") as f: # w mode ile her seferinde baştan yaz
        for entry in config.chat_history:
            f.write(f"{entry['role']}:{entry['content']}\n")

def save_found_programs():
    """Bulunan kullanıcı programlar listesini JSON dosyasına kaydeder."""
    with open(config.PROGRAM_LIST_FILE, "w", encoding="utf-8") as f:
        json.dump(config.found_programs, f, indent=2, ensure_ascii=False)

def save_system_programs():
    """Bulunan sistem programlar listesini JSON dosyasına kaydeder."""
    with open(config.SYSTEM_PROGRAM_LIST_FILE, "w", encoding="utf-8") as f:
        json.dump(config.system_programs, f, indent=2, ensure_ascii=False)

def save_all_data():
    """Tüm kalıcı verileri kaydeder."""
    save_profile()
    save_aliases()
    save_macros()
    save_history()
    save_found_programs()
    save_system_programs()

# === ALIAS VE MAKRO İŞLEMLERİ (config'deki global değişkenleri kullanacak) ===
def add_alias(alias, command):
    """Yeni bir takma ad ekler."""
    config.aliases[alias] = command
    save_aliases()
    return f"Alias '{alias}' kaydedildi."

def run_alias(alias):
    """Kayıtlı bir takma adı çalıştırır."""
    if alias in config.aliases:
        # Local shell command execution function
        return run_shell_command(config.aliases[alias])
    else:
        return "Alias bulunamadı."

def delete_alias(alias):
    """Bir takma adı siler."""
    if alias in config.aliases:
        del config.aliases[alias]
        save_aliases()
        return f"Alias '{alias}' silindi."
    else:
        return "Alias bulunamadı."

def add_macro(name, commands):
    """Yeni bir makro ekler."""
    config.macros[name] = commands
    save_macros()
    return f"Makro '{name}' kaydedildi."

def run_macro(name):
    """Kayıtlı bir makroyu çalıştırır."""
    if name not in config.macros:
        return "Makro bulunamadı."
    results = []
    for cmd in config.macros[name]:
        # Local shell command execution function
        results.append(run_shell_command(cmd))
    return "\n".join(results)

def delete_macro(name):
    """Bir makroyu siler."""
    if name in config.macros:
        del config.macros[name]
        save_macros()
        return f"Makro '{name}' silindi."
    else:
        return "Makro bulunamadı."
