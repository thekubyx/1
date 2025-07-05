# plugins/örnek_plugin.py
# Bu bir eklenti dosyasıdır.

def plugin_entry(data):
    """
    Bu fonksiyon eklentinin giriş noktasıdır.
    'kullan örnek_plugin <veri>' komutuyla çağrılır.
    """
    return f"Eklenti 'örnek_plugin' çalıştı. Veri: '{data}'"

# Diğer yardımcı fonksiyonlar eklentinin içinde olabilir
def _private_helper_function():
    pass
