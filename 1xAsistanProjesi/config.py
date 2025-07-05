import os
import platform
import datetime
import getpass

# === LLM Ayarları ===
DEFAULT_LLM_API = "http://localhost:11434/api/generate"
# Ollama'ya eklediğiniz modelleri buraya ekleyebilirsiniz. tinyllama yüklü olduğundan burada yer alıyor.
LLM_MODELS = ["llama3", "mistral", "phi3", "tinyllama"]
DEFAULT_LLM_MODEL = "mistral" # Asistanın varsayılan olarak kullanacağı model

# === Genel Ayarlar ===
ENABLE_SPEECH = False # Sesli yanıt varsayılan olarak kapalı
MAX_HISTORY = 40      # Sohbet geçmişi tutulacak maksimum satır sayısı
PLUGIN_FOLDER = "plugins" # Eklentilerin bulunduğu klas

# === Sabit Sistem Araçları ===
SYSTEM_TOOLS = {
    "kayıt defteri": "regedit",
    "hizmetler": "services.msc",
    "görev yöneticisi": "taskmgr",
    "grup ilkesi": "gpedit.msc", # Windows Home sürümlerinde bulunmayabilir
    "olay görüntüleyici": "eventvwr.msc",
    "bilgisayar yönetimi": "compmgmt.msc",
    "disk yönetimi": "diskmgmt.msc",
    "aygıt yöneticisi": "devmgmt.msc",
    "sistem yapılandırması": "msconfig",
    "güvenlik duvarı": "wf.msc",
    "ağ bağlantıları": "ncpa.cpl",
    "sistem bilgisi aracı": "msinfo32",
    "program ekle kaldır": "appwiz.cpl",
    "denetim masası": "control",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "calc": "calc.exe", # Hesap Makinesi
    "notepad": "notepad.exe", # Not Defteri
    "paint": "mspaint.exe", # Paint
}

# Windows Servisleri Kategorizasyonu (Manuel olarak doldurulacak)
# 'Kapatılabilir', 'Riskli', 'Kapatılmamalı', 'Bilinmiyor'
WINDOWS_SERVICE_CATEGORIES = {
    "BITS": {
        "description": "Arka Plan Akıllı Aktarım Hizmeti. Dosya indirmelerini ve yüklemelerini yönetir. Windows Update için gereklidir.",
        "category": "Kapatılmamalı",
        "notes": "Çoğu uygulama ve Windows güncellemeleri için kritik."
    },
    "Dnscache": {
        "description": "DNS istemcisi. DNS adlarını önbelleğe alarak ağ performansını artırır.",
        "category": "Kapatılabilir",
        "notes": "Kapatılırsa DNS çözümlemesi yavaşlayabilir ancak internet çalışmaya devam eder. Sorun giderirken kapatılabilir."
    },
    "Spooler": {
        "description": "Yazdırma Biriktiricisi. Yazdırma işlerini yönetir.",
        "category": "Kapatılabilir",
        "notes": "Yazıcı kullanmıyorsanız kapatılabilir. Kapatılırsa yazıcılar çalışmaz."
    },
    "WSearch": {
        "description": "Windows Search. Dosya dizinleme ve arama hizmeti.",
        "category": "Kapatılabilir",
        "notes": "Dosya aramayı sık kullanmıyorsanız kapatılabilir. RAM ve CPU kullanımını düşürebilir."
    },
    "Themes": {
        "description": "Temalar hizmeti. Windows temalarını ve görsel stillerini yönetir.",
        "category": "Kapatılabilir",
        "notes": "Klasik görünüme geçerek kapatılabilir, çok az performans artışı sağlayabilir."
    },
    "wuauserv": {
        "description": "Windows Update. Windows güncellemelerinin tespitini, indirilmesini ve yüklenmesini sağlar.",
        "category": "Kapatılmamalı",
        "notes": "Güvenlik güncellemeleri ve sistem kararlılığı için kritik. Ancak manuel kontrol için geçici olarak durdurulabilir."
    },
    "LanmanServer": {
        "description": "Sunucu Hizmeti. Dosya, yazıcı ve adlandırılmış kanal paylaşımını etkinleştirir.",
        "category": "Riskli",
        "notes": "Ağ üzerinden dosya paylaşımı yapmıyorsanız kapatılabilir, ancak bazı ağ işlevlerini etkileyebilir."
    },
    "TeamViewer": {
        "description": "TeamViewer uzaktan erişim yazılımının servisidir.",
        "category": "Kapatılabilir",
        "notes": "Uzaktan bağlantı kullanmadığınızda kapatılabilir. Güvenlik ve performans için faydalı olabilir."
    },
    "MongoDB": { # Örnek bir uygulama servisi
        "description": "MongoDB veritabanı sunucusunu çalıştırır.",
        "category": "Kapatılabilir",
        "notes": "MongoDB tabanlı uygulamalar kullanmıyorsanız durdurulabilir."
    },
    "SQLBrowser": { # Örnek bir SQL servisi
        "description": "SQL Server örnekleri hakkında bilgi sağlar.",
        "category": "Kapatılabilir",
        "notes": "SQL Server kullanmıyorsanız veya yerel ağda veritabanı bulmaya ihtiyacınız yoksa kapatılabilir."
    },
    # Buraya ek servisler ekleyebilirsin. Servis adlarının Windows'taki 'Name' alanıyla eşleştiğinden emin ol!
}


# === Dosya Yolları ===
PROFILE_FILE = "user_profile.json"
ALIASES_FILE = "aliases.json"
MACRO_FILE = "macros.json"
CHAT_HISTORY_FILE = "chat_history.txt"
PROGRAM_LIST_FILE = "found_programs.json"        # Kullanıcı programları
SYSTEM_PROGRAM_LIST_FILE = "system_programs.json" # Sistem programları

# === Program Arama Yolları ===
PROGRAM_SEARCH_PATHS = [ # Kullanıcı programları için aranacak temel yollar
    os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files")),
    os.path.join(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")),
    os.path.join(os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming")), "Microsoft\\Windows\\Start Menu\\Programs"),
    os.path.join(os.environ.get("ALLUSERSPROFILE", "C:\\ProgramData"), "Microsoft\\Windows\\Start Menu\\Programs"),
    os.path.expanduser("~\\Desktop")
]

SYSTEM_PROGRAM_SEARCH_PATHS = [ # Sistem uygulamaları için aranacak yollar
    os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "System32"),
    os.path.join(os.environ.get("WINDIR", "C:\\Windows")),
    # Buraya eklemek isterseniz, diğer sistem yollarını da ekleyebilirsiniz.
    # Örneğin: os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "SysWOW64") # 64-bit sistemlerde 32-bit uygulamalar için
]

# === GLOBAL DURUM DEĞİŞKENLERİ ===
# Bu değişkenler, programın genelinde durum bilgisini tutar ve
# diğer modüller tarafından değiştirilebilir veya okunabilir.
chat_history = []
user_profile = {} # data_manager tarafından yüklenecek
aliases = {}      # data_manager tarafından yüklenecek
macros = {}       # data_manager tarafından yüklenecek
found_programs = {} # program_manager tarafından doldurulacak
system_programs = {} # program_manager tarafından doldurulacak

system_os = platform.system()
current_llm = DEFAULT_LLM_MODEL # <<< BURASI DA ARTIK DEFAULT_LLM_MODEL'İ KULLANIYOR!
