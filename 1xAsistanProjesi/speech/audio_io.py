# speech/audio_io.py
import os

try:
    import speech_recognition as sr
    import pyttsx3
    from gtts import gTTS
    import playsound
    VOICE_MODULES = True
except ImportError:
    VOICE_MODULES = False
    # print("Uyarı: Sesli mod modülleri (speech_recognition, pyttsx3, gtts, playsound) bulunamadı. Sesli komutlar devre dışı.")

import config # config dosyasındaki ENABLE_SPEECH değerine erişim için

def speak(text):
    """Metni sesli olarak söyler."""
    if not config.ENABLE_SPEECH or not VOICE_MODULES:
        return
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception:
        # pyttsx3 çalışmazsa gTTS kullanmaya çalış
        try:
            tts = gTTS(text=text, lang='tr')
            filename = "temp_voice.mp3"
            tts.save(filename)
            playsound.playsound(filename)
            os.remove(filename)
        except Exception as e:
            # print(f"Sesli yanıt üretilemedi: {e}") # Debug için
            pass

def listen():
    """Sesli komutları dinler ve metne dönüştürür."""
    if not config.ENABLE_SPEECH or not VOICE_MODULES:
        return "" # Sesli mod kapalıysa veya modüller yoksa boş string döndür

    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Dinliyorum...")
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=5) # Dinleme süresi
        except sr.WaitTimeoutError:
            return "" # Ses gelmezse zaman aşımı
        except Exception as e:
            print(f"Mikrofondan ses alınamadı: {e}")
            return ""
    try:
        # Türkçe dilini belirt
        return r.recognize_google(audio, language="tr-TR")
    except sr.UnknownValueError:
        print("Ses algılanamadı, lütfen tekrar deneyin.")
        return ""
    except sr.RequestError as e:
        print(f"Google Speech Recognition servisine ulaşılamadı: {e}")
        return ""
    except Exception as e:
        print(f"Ses tanıma hatası: {e}")
        return ""
