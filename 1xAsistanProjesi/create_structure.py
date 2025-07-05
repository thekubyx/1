# create_structure.py
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

folders = [
    "core",
    "llm",
    "speech",
    "persistence",
    "plugins"
]

for folder in folders:
    path = os.path.join(base_dir, folder)
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "__init__.py"), "w") as f:
        pass # Boş init.py dosyası oluştur

print("Klasör yapısı ve __init__.py dosyaları başarıyla oluşturuldu.")
print("Şimdi verdiğim Python kodlarını ilgili dosyalara kopyalayıp yapıştırabilirsiniz.")
