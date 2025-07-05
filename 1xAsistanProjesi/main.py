# Bu dosya, asistanınızın tüm ana mantığını içerir.
# Herhangi bir harici modül import edilmesine gerek yoktur.

import speech_recognition as sr
import pyttsx3
import ollama
import json
import os
import datetime
import random
import time
import threading
import subprocess
import sys
import requests # check_ollama_server için eklendi

# --- Ayarlar ve Yapılandırma ---
config = {
    "MASTER_NAME": "Kubyx",
    "ASSISTANT_NAME": "Mira",
    "WAKE_WORD": "mira",
    "OLLAMA_MODEL": "mistral:latest", # Düzeltildi
    "ENABLE_SPEECH": False,
    "VOICE_MODULES": True,
    "OLLAMA_SERVER_URL": "http://localhost:11434",
    "CHAT_HISTORY_FILE": "chat_history.json",
    "USER_PROFILE_FILE": "user_profile.json",
    "LLM_TEMPERATURE": 0.7,
    "LLM_TOP_P": 0.9,
    "LLM_MAX_TOKENS": 2048,
    "STT_THRESHOLD": 0.7,
    "TTS_VOICE_ID": None, # Düzeltildi
    "TTS_RATE": 180,
    "TTS_VOLUME": 1.0
}

# --- Ollama Modeli Bağlantısı ve Kontrolü ---
def check_ollama_server():
    print(f"Ollama sunucusu kontrol ediliyor: {config['OLLAMA_SERVER_URL']}")
    try:
        response = requests.get(f"{config['OLLAMA_SERVER_URL']}/api/tags", timeout=5)
        response.raise_for_status()  # HTTP hataları için
        models = [model['name'] for model in response.json()['models']]
        print(f"Mevcut Ollama modelleri: {', '.join(models)}")
        if config['OLLAMA_MODEL'] not in models:
            print(f"Uyarı: Ayarlanan model '{config['OLLAMA_MODEL']}' sunucuda bulunamadı.")
            return False
        return True
    except requests.exceptions.ConnectionError:
        print("Hata: Ollama sunucusuna bağlanılamıyor. Çalıştığından emin olun.")
        return False
    except requests.exceptions.Timeout:
        print("Hata: Ollama sunucusu zaman aşımına uğradı. Ağ bağlantınızı kontrol edin.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Ollama sunucusu kontrol edilirken bir hata oluştu: {e}")
        return False
    except Exception as e:
        print(f"Beklenmeyen bir hata oluştu: {e}")
        return False

def start_ollama_server():
    print("Ollama sunucusu otomatik olarak başlatılıyor...")
    try:
        if sys.platform.startswith('win'):
            subprocess.Popen(['start', 'ollama', 'run', config['OLLAMA_MODEL']], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
        elif sys.platform.startswith('linux') or sys.platform == 'darwin':
            subprocess.Popen(['x-terminal-emulator', '-e', f'ollama run {config["OLLAMA_MODEL"]}'] if sys.platform.startswith('linux') else ['osascript', '-e', f'tell app "Terminal" to do script "ollama run {config["OLLAMA_MODEL"]}"'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Ollama sunucusunun başlaması için lütfen bekleyiniz...")
        time.sleep(10) # Sunucunun başlaması için bekle
        if check_ollama_server():
            print("Ollama sunucusu başarıyla başlatıldı ve model yüklendi.")
        else:
            print("Ollama sunucusu başlatılamadı veya model yüklenemedi. Lütfen elle kontrol edin.")
    except FileNotFoundError:
        print("Hata: 'ollama' komutu bulunamadı. Ollama'nın yüklü olduğundan ve PATH'inizde olduğundan emin olun.")
    except Exception as e:
        print(f"Ollama sunucusunu başlatırken beklenmeyen bir hata oluştu: {e}")


def ollama_ask_llm(prompt, chat_history):
    if not check_ollama_server():
        print("Ollama sunucusu çalışmıyor veya modele erişilemiyor. Komut işlenemiyor.")
        return "Üzgünüm, şu anda benimle konuşamıyorum. Ollama sunucusunda bir sorun var gibi görünüyor."

    messages = [
        {"role": "user", "content": prompt}
    ]
    
    for chat_item in chat_history:
        messages.append({"role": chat_item["role"], "content": chat_item["content"]})

    try:
        print(f"LLM'e gönderilen prompt: {prompt}")
        print(f"LLM'e gönderilen mesaj geçmişi: {chat_history}")

        response = ollama.chat(
            model=config["OLLAMA_MODEL"],
            messages=messages,
            options={
                "temperature": config["LLM_TEMPERATURE"],
                "top_p": config["LLM_TOP_P"],
                "num_predict": config["LLM_MAX_TOKENS"]
            }
        )
        full_response = response['message']['content'].strip()
        return full_response

    except ollama.ResponseError as e:
        print(f"Ollama yanıt hatası: {e}")
        if "not found" in str(e):
            print(f"Model '{config['OLLAMA_MODEL']}' bulunamadı. Lütfen 'ollama pull {config['OLLAMA_MODEL']}' komutuyla modeli indirin.")
            return f"Üzgünüm, '{config['OLLAMA_MODEL']}' modeli bulunamadı. Lütfen modeli indirdiğinizden emin olun."
        return "Üzgünüm, Ollama'dan bir yanıt alırken bir hata oluştu."
    except Exception as e:
        print(f"Beklenmeyen bir hata oluştu: {e}")
        return "Üzgünüm, bir sorun oluştu ve yanıt veremiyorum."

# --- Ses Giriş/Çıkış Modülü ---
def speak(text):
    if not config["ENABLE_SPEECH"] or not config["VOICE_MODULES"]:
        print(f"[SES KAPALI] Asistan: {text}")
        return

    print(f"Asistan: {text}")
    engine = pyttsx3.init()
    if config["TTS_VOICE_ID"]:
        voices = engine.getProperty('voices')
        found_voice = False
        for voice in voices:
            if config["TTS_VOICE_ID"].lower() in voice.name.lower() or \
               config["TTS_VOICE_ID"].lower() in voice.id.lower():
                engine.setProperty('voice', voice.id)
                found_voice = True
                break
        if not found_voice:
            print(f"Uyarı: '{config['TTS_VOICE_ID']}' ses kimliği bulunamadı. Varsayılan ses kullanılıyor.")
    
    engine.setProperty('rate', config["TTS_RATE"])
    engine.setProperty('volume', config["TTS_VOLUME"])
    engine.say(text)
    engine.runAndWait()

def listen():
    if not config["ENABLE_SPEECH"] or not config["VOICE_MODULES"]:
        print("[SES KAPALI] Sesli komut dinlenmiyor.")
        return ""

    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        print("Dinliyorum...")
        audio = r.listen(source, phrase_time_limit=5) # 5 saniye bekleme limiti

    try:
        print("Tanımlanıyor...")
        text = r.recognize_google(audio, language="tr-TR")
        print(f"Sen: {text}")
        return text.lower()
    except sr.UnknownValueError:
        print("Üzgünüm, ne dediğini anlayamadım.")
        return ""
    except sr.RequestError as e:
        print(f"Google Speech Recognition hizmetine ulaşılamadı; {e}")
        return ""
    except Exception as e:
        print(f"Ses tanıma sırasında beklenmeyen bir hata oluştu: {e}")
        return ""

def wake_word_listener():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        print(f"{config['ASSISTANT_NAME']} uyandırma kelimesi bekleniyor...")
        audio = r.listen(source)
    try:
        text = r.recognize_google(audio, language="tr-TR")
        if config["WAKE_WORD"] in text.lower():
            print(f"{config['ASSISTANT_NAME']} uyandı!")
            return True
        return False
    except sr.UnknownValueError:
        return False
    except sr.RequestError as e:
        return False

# --- Veri Yönetimi ---
chat_history = []
user_profile = {}

def load_data():
    global chat_history, user_profile
    try:
        if os.path.exists(config["CHAT_HISTORY_FILE"]):
            with open(config["CHAT_HISTORY_FILE"], 'r', encoding='utf-8') as f:
                chat_history = json.load(f)
        else:
            chat_history = []
        
        if os.path.exists(config["USER_PROFILE_FILE"]):
            with open(config["USER_PROFILE_FILE"], 'r', encoding='utf-8') as f:
                user_profile = json.load(f)
        else:
            user_profile = {"name": config["MASTER_NAME"], "last_seen": str(datetime.datetime.now())}
        
        print("Veriler yüklendi.")
    except json.JSONDecodeError:
        print("Uyarı: Sohbet geçmişi veya kullanıcı profili dosyası bozuk. Yeniden oluşturuluyor.")
        chat_history = []
        user_profile = {"name": config["MASTER_NAME"], "last_seen": str(datetime.datetime.now())}
    except Exception as e:
        print(f"Veriler yüklenirken hata oluştu: {e}")
        chat_history = []
        user_profile = {"name": config["MASTER_NAME"], "last_seen": str(datetime.datetime.now())}

def save_data():
    try:
        with open(config["CHAT_HISTORY_FILE"], 'w', encoding='utf-8') as f:
            json.dump(chat_history, f, ensure_ascii=False, indent=4)
        with open(config["USER_PROFILE_FILE"], 'w', encoding='utf-8') as f:
            json.dump(user_profile, f, ensure_ascii=False, indent=4)
        print("Veriler kaydedildi.")
    except Exception as e:
        print(f"Veriler kaydedilirken hata oluştu: {e}")

# --- Komut İşleme ve Yönetimi ---
def execute_command(command_text):
    command_text = command_text.lower()
    response = ""

    if "saat kaç" in command_text:
        response = datetime.datetime.now().strftime("%H:%M")
    elif "tarih ne" in command_text or "bugün ayın kaçı" in command_text:
        response = datetime.datetime.now().strftime("%d %B %Y")
    elif "merhaba" in command_text or "selam" in command_text:
        response = f"Merhaba {user_profile.get('name', 'efendim')}, size nasıl yardımcı olabilirim?"
    elif "kendini tanıt" in command_text:
        response = f"Ben {config['ASSISTANT_NAME']}, {user_profile.get('name', 'size')} yardımcı olmak için tasarlanmış bir yapay zeka asistanıyım."
    elif "nasılsın" in command_text:
        response = "Ben bir yapay zekayım, bir hissim yok. Ama sizin iyi olduğunuzu umuyorum."
    elif "teşekkür ederim" in command_text or "sağ ol" in command_text:
        response = "Rica ederim, her zaman hizmetinizdeyim."
    elif "uygulamayı aç" in command_text:
        app_name = command_text.replace("uygulamayı aç", "").strip()
        if "google" in app_name:
            response = "Google Chrome açılıyor."
            os.startfile("chrome")
        elif "notepad" in app_name:
            response = "Notepad açılıyor."
            os.startfile("notepad")
        else:
            response = f"Üzgünüm, {app_name} uygulamasını bulamadım veya nasıl açacağımı bilmiyorum."
    elif "kapat" in command_text and "uygulamayı" in command_text:
        response = "Üzgünüm, henüz uygulama kapatma yeteneğim yok."
    elif "arama yap" in command_text or "internet'te ara" in command_text:
        query = command_text.replace("arama yap", "").replace("internet'te ara", "").strip()
        if query:
            import webbrowser
            search_url = f"https://www.google.com/search?q={query}"
            webbrowser.open(search_url)
            response = f"{query} için internette arama yapılıyor."
        else:
            response = "Ne aramamı istersiniz?"
    elif "youtube aç" in command_text:
        import webbrowser
        webbrowser.open("http://youtube.com")
        response = "YouTube açılıyor."
    elif "müzik çal" in command_text:
        response = "Üzgünüm, henüz müzik çalma yeteneğim yok. Ama YouTube'dan arama yapabilirim."
    elif "bilgisayarı kapat" in command_text or "bilgisayarı yeniden başlat" in command_text:
        response = "Bu komutlar için iznim yok ve sistem güvenliği nedeniyle doğrudan bu işlemleri yapmam önerilmez."
    elif "yardım" in command_text:
        response = "Size zaman, tarih verebilirim, uygulama açabilirim veya internette arama yapabilirim. Başka ne yapabilirim öğrenmek için konuşmaya devam edin."
    elif "dur" in command_text or "kapat kendini" in command_text or "çıkış" in command_text:
        response = "Görüşmek üzere, kendinize iyi bakın!"
        speak(response)
        save_data()
        sys.exit()
    else:
        print(f"LLM için komut: {command_text}")
        response = ollama_ask_llm(command_text, chat_history) # Burası doğru chat_history olmalı

    return response


# --- Ana Döngü (Asistanın Çalıştığı Kısım) ---
def main():
    print(f"{config['ASSISTANT_NAME']} başlatılıyor...")
    load_data()
    
    if not check_ollama_server():
        start_ollama_server()
        if not check_ollama_server():
            print("Ollama sunucusu hala çalışmıyor. Lütfen elle kontrol edin ve uygulamayı yeniden başlatın.")
            speak("Ollama sunucusuna bağlanamıyorum, lütfen sunucuyu kontrol edin.")
            sys.exit()

    speak(f"Merhaba {user_profile.get('name', 'efendim')}. Nasılsınız?")
    
    while True:
        user_input = ""
        try:
            if config["ENABLE_SPEECH"]:
                user_input = listen()
            else:
                user_input = input("Komutunuzu yazın (veya 'yardım'): ").strip().lower()

            if not user_input:
                if config["ENABLE_SPEECH"] and config["VOICE_MODULES"]:
                    if wake_word_listener():
                        speak("Buyurun.")
                        user_input = listen()
                        if not user_input:
                            continue
                    else:
                        continue
                else:
                    continue
            
            print(f"Gelen komut: {user_input}")

            if "çalıştır" in user_input and config["ASSISTANT_NAME"].lower() in user_input:
                command_to_execute = user_input.replace(f"{config['ASSISTANT_NAME'].lower()} çalıştır", "").strip()
                if command_to_execute:
                    reply = ollama_ask_llm(command_to_execute, chat_history)
                    speak(reply)
                    chat_history.append({"role": "user", "content": command_to_execute})
                    chat_history.append({"role": "assistant", "content": reply})
            elif "çalıştır" in user_input:
                command_to_execute = user_input.replace("çalıştır", "").strip()
                if command_to_execute:
                    reply = ollama_ask_llm(command_to_execute, chat_history)
                    speak(reply)
                    chat_history.append({"role": "user", "content": command_to_execute})
                    chat_history.append({"role": "assistant", "content": reply})
            else:
                reply = execute_command(user_input)
                # execute_command'in kendi başına bir yanıt üretip üretmediğini kontrol etmek zor olduğu için
                # en basit yol olarak her zaman chat_history'ye ekleyelim.
                # Eğer LLM'e gittiyse, LLM fonksiyonu zaten ekliyor olmalı.
                # Burada sadece yerel komutlar için ekleyelim.
                if reply: # Boş yanıt dönmediyse
                    # LLM'e gitmeyen komutlar için chat_history'ye ekleme
                    if not ("Üzgünüm, şu anda benimle konuşamıyorum. Ollama sunucusunda bir sorun var gibi görünüyor." in reply or \
                            "Üzgünüm, Ollama'dan bir yanıt alırken bir hata oluştu." in reply or \
                            "Üzgünüm, bir sorun oluştu ve yanıt veremiyorum." in reply or \
                            "Üzgünüm, 'mistral:latest' modeli bulunamadı. Lütfen modeli indirdiğinizden emin olun." in reply):
                        chat_history.append({"role": "user", "content": user_input})
                        chat_history.append({"role": "assistant", "content": reply})
                speak(reply)


        except KeyboardInterrupt:
            print("\nKapatılıyor...")
            speak("Kapatılıyor.") # speak() fonksiyonu config'i kullanır, audio_io'ya gerek yok
            save_data() # save_data() fonksiyonu global chat_history kullanır
            break
        except Exception as e:
            print(f"Beklenmeyen bir hata oluştu: {e}")

# Programın başlangıç noktası
if __name__ == "__main__":
    main()
