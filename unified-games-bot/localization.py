import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

class Localization:
    """Система локалізації для бота"""
    
    def __init__(self):
        self.locales_dir = Path(__file__).parent / "locales"
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.load_translations()
    
    def load_translations(self):
        """Завантажити всі переклади"""
        for locale_file in self.locales_dir.glob("*.json"):
            locale = locale_file.stem
            try:
                with open(locale_file, 'r', encoding='utf-8') as f:
                    self.translations[locale] = json.load(f)
            except Exception as e:
                print(f"Error loading locale {locale}: {e}")
    
    def get_text(self, locale: str, key: str, **kwargs) -> str:
        """Отримати переклад за ключем з підстановкою параметрів"""
        if locale not in self.translations:
            locale = "uk"  # Fallback to Ukrainian
        
        # Розбиваємо ключ на частини (наприклад: "bot.welcome")
        keys = key.split('.')
        value = self.translations[locale]
        
        try:
            for k in keys:
                value = value[k]
        except (KeyError, TypeError):
            # Fallback to Ukrainian
            if locale != "uk":
                return self.get_text("uk", key, **kwargs)
            return f"Missing translation: {key}"
        
        # Підставляємо параметри
        if isinstance(value, str) and kwargs:
            try:
                return value.format(**kwargs)
            except KeyError:
                return value
        
        return str(value)
    
    def get_available_locales(self) -> list:
        """Отримати список доступних мов"""
        return list(self.translations.keys())
    
    def is_valid_locale(self, locale: str) -> bool:
        """Перевірити чи існує мова"""
        return locale in self.translations

# Глобальний екземпляр локалізації
localization = Localization()

def get_text(locale: str, key: str, **kwargs) -> str:
    """Зручна функція для отримання перекладу"""
    return localization.get_text(locale, key, **kwargs)

def get_user_language(user_id: int) -> str:
    """Отримати мову користувача (з бази даних або за замовчуванням)"""
    # TODO: Реалізувати збереження мови користувача в БД
    # Поки що повертаємо українську за замовчуванням
    return "uk"

def set_user_language(user_id: int, language: str) -> bool:
    """Встановити мову користувача"""
    # TODO: Реалізувати збереження мови користувача в БД
    return localization.is_valid_locale(language) 