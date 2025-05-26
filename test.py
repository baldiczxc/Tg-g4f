from deep_translator import GoogleTranslator

text = 'Привет мир'

# Автоматическое определение языка, перевод на немецкий (по названию)
translated1 = GoogleTranslator(source='auto', target='german').translate(text=text)
print(translated1)

# Автоматическое определение языка, перевод на немецкий (по аббревиатуре)
translated2 = GoogleTranslator(source='auto', target='de').translate(text=text)
print(translated2)

# Явно указанные языки по аббревиатуре
translated3 = GoogleTranslator(source='ru', target='en').translate(text=text)
print(translated3)
