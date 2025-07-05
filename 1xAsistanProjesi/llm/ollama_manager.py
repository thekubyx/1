import requests
import subprocess
import os
import shutil
import json # JSON modülünü import ettiğinizden emin olun!

import config # config dosyasındaki sabitlere erişim için

def ask_llm(prompt, history=None, model=None):
    """LLM API'ye (Ollama) soru sorar."""
    url = config.DEFAULT_LLM_API
    # DÜZELTİLDİ: config.py'deki DEFAULT_LLM_MODEL değişkenini kullanıyoruz
    model = model or config.DEFAULT_LLM_MODEL # Varsayılan modeli config'den al
    
    # Ollama'ya gönderilecek payload'ı hazırla
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True, # Bu KISIM ARTIK TRUE olarak ayarlandı
        "options": {"temperature": 0.25}
    }
    
    # Eğer geçmiş (history) varsa, mesajlar formatını kullan
    if history:
        # Geçmişi LLM formatına uygun hale getir
        # NOTE: Ollama'nın API'sinde 'messages' kullanıldığında 'prompt' alanı gönderilmez.
        # Bu nedenle, payload'ı buna göre ayarlıyoruz.
        formatted_history = [{"role": entry["role"], "content": entry["content"]} for entry in history[-config.MAX_HISTORY:]]
        payload["messages"] = formatted_history + [{"role": "user", "content": prompt}] # Yeni istemi de ekle
        del payload["prompt"] # 'messages' kullanılıyorsa 'prompt' kaldırılır
    
    try:
        # Ollama API'sine POST isteği gönder
        r = requests.post(url, json=payload, timeout=180)
        r.raise_for_status() # HTTP hatalarını yakala (örn. 404 Not Found, 500 Internal Server Error)

        full_response_content = ""
        # Ollama'dan gelen yanıtı satır satır (stream olarak) oku ve işle
        for chunk in r.iter_lines(): 
            if chunk:
                try:
                    # Gelen veriyi UTF-8 olarak decode et ve JSON olarak ayrıştır
                    json_data = json.loads(chunk.decode('utf-8'))
                    
                    # --- HATA AYIKLAMA İÇİN EKLEYİN ---
                    # Her bir JSON chunk'ını görmek için bu satırın başındaki # işaretini SİLİNDİ.
                    print(f"DEBUG LLM Chunk: {json_data}") # <<< BURADAKİ DİYES KALDIRILDI!
                    # --- HATA AYIKLAMA İÇİN EKLEYİN ---

                    content_in_this_chunk = ""
                    if "response" in json_data: # Bazı eski Ollama versiyonları veya formatları için
                        content_in_this_chunk = json_data["response"]
                    elif "message" in json_data and "content" in json_data["message"]: # Güncel Ollama formatı için
                        content_in_this_chunk = json_data["message"]["content"]
                    
                    full_response_content += content_in_this_chunk # İçeriği her zaman ekle

                    # Eğer yanıtın sonuna geldiysek (Ollama'nın "done" bayrağı), döngüden çık
                    # Yalnızca 'done' true ise VE bu 'done' chunk'ında herhangi bir içerik olmadıysa VEYA 
                    # 'done_reason' 'load' dışında bir şeyse (gerçek bir bitiş sinyali) döngüyü kır.
                    # Aksi takdirde, done true olsa bile eğer response boşsa ve done_reason 'load' ise devam et.
                    if json_data.get("done"):
                        # Eğer bu 'done' chunk'ında hiç içerik yoksa VE 'done_reason' 'load' ise,
                        # bu muhtemelen bir başlangıç durumu sinyalidir, döngüye devam et.
                        if not content_in_this_chunk and json_data.get("done_reason") == 'load':
                            pass # Döngüye devam et, break yapma
                        else:
                            # Ya bu 'done' chunk'ında içerik vardı, ya da 'done_reason' bir bitiş sinyaliydi.
                            break # Döngüyü kır
                            
                except json.JSONDecodeError:
                    # Bazen kısmi veya bozuk JSON chunk'ları gelebilir, bunları sessizce atla.
                    # Eğer hata ayıklamak isterseniz aşağıdaki satırı aktif edebilirsiniz:
                    # print(f"DEBUG: JSONDecodeError at chunk: {chunk.decode('utf-8', errors='ignore')}")
                    continue
                except Exception as e:
                    # JSON işleme sırasında oluşabilecek diğer beklenmedik hataları yakala
                    print(f"DEBUG: JSON işleme sırasında beklenmeyen hata: {e} - Orijinal Chunk: {chunk.decode('utf-8', errors='ignore')}")
                    continue

        return full_response_content.strip() # Tüm yanıtı temizleyip döndür

    except requests.exceptions.Timeout:
        # İstek zaman aşımına uğradığında
        return "LLM API zaman aşımına uğradı. Lütfen daha sonra tekrar deneyin."
    except requests.exceptions.RequestException as e:
        # Ağ bağlantısı sorunları veya HTTP hataları (4xx/5xx)
        # Eğer r nesnesi bir status_code'a sahipse, onu da hata mesajına ekle
        if hasattr(r, 'status_code'): 
            return f"LLM API bağlantı hatası: {e} (HTTP Durum Kodu: {r.status_code})"
        return f"LLM API bağlantı hatası: {e}"
    except Exception as e:
        # LLM yanıtını işlerken oluşabilecek diğer bilinmeyen hatalar
        return f"LLM API'den yanıt alınırken bilinmeyen bir hata oluştu: {e}"

def ollama_create_model_from_gguf(gguf_path, model_name):
    """
    HuggingFace'den indirilen GGUF dosyasını Ollama'ya model olarak ekler.
    """
    if not os.path.exists(gguf_path):
        return f"GGUF dosyası bulunamadı: {gguf_path}"
    if not shutil.which("ollama"):
        return "Ollama yüklü değil veya PATH'de değil! Lütfen Ollama'yı yükleyin ve PATH'inize ekleyin."
    
    # Modelfile oluştur
    # TEMPLATE kısmı, LLM'in kullanıcı girişini nasıl yorumlaması gerektiğini belirler.
    # Eğer modeliniz farklı bir prompt formatı bekliyorsa burayı düzenlemeniz gerekebilir.
    modelfile_content = f'FROM ./{os.path.basename(gguf_path)}\nTEMPLATE """{{ .Prompt }}"""\n' 
    modelfile_path = os.path.join(os.path.dirname(gguf_path), "Modelfile")
    try:
        with open(modelfile_path, "w", encoding="utf-8") as f:
            f.write(modelfile_content)
    except Exception as e:
        return f"Modelfile yazılamadı: {e}"
    
    # Ollama create komutunu çalıştır
    prev_dir = os.getcwd() # Mevcut çalışma dizinini kaydet
    try:
        os.chdir(os.path.dirname(gguf_path)) # GGUF dosyasının dizinine geç
        # "ollama create <model_name> --file Modelfile" komutu
        result = subprocess.run(
            ["ollama", "create", model_name, "--file", "os.path.basename(modelfile_path)"], # Dosya adını kullan
            capture_output=True, text=True, timeout=1200 # 20 dakika zaman aşımı
        )
        os.chdir(prev_dir) # Orijinal çalışma dizinine geri dön

        if result.returncode == 0:
            if model_name not in config.LLM_MODELS:
                config.LLM_MODELS.append(model_name) # Yeni modeli config'e ekle
            return f"Model '{model_name}' başarıyla eklendi ve Ollama ile kullanılabilir!"
        else:
            return f"Ollama create hatası:\n{result.stderr}"
    except Exception as e:
        return f"Ollama model ekleme hatası: {e}"

def ollama_list_models():
    """
    Ollama'da kayıtlı modelleri listeler.
    """
    if not shutil.which("ollama"):
        return "Ollama yüklü değil veya PATH'de değil! Lütfen Ollama'yı yükleyin ve PATH'inize ekleyin."
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Ollama list hatası:\n{result.stderr}"
    except Exception as e:
        return f"Ollama model listesi hatası: {e}"
