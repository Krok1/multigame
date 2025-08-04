from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from localization import get_text

def get_main_menu_keyboard(locale: str = "uk") -> InlineKeyboardMarkup:
    """Головне меню з вибором гри"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text=get_text(locale, "buttons.buckshot"), 
        callback_data="game_buckshot"
    ))
    builder.add(InlineKeyboardButton(
        text=get_text(locale, "buttons.blackjack"), 
        callback_data="game_blackjack"
    ))
    builder.add(InlineKeyboardButton(
        text=get_text(locale, "buttons.rules"), 
        callback_data="rules"
    ))
    builder.add(InlineKeyboardButton(
        text=get_text(locale, "buttons.help"), 
        callback_data="help"
    ))
    builder.add(InlineKeyboardButton(
        text=get_text(locale, "buttons.language"), 
        callback_data="language"
    ))
    
    builder.adjust(2)  # 2 кнопки в ряд
    return builder.as_markup()

def get_language_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура вибору мови"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text=get_text("uk", "buttons.ukrainian"), 
        callback_data="lang_uk"
    ))
    builder.add(InlineKeyboardButton(
        text=get_text("ru", "buttons.russian"), 
        callback_data="lang_ru"
    ))
    builder.add(InlineKeyboardButton(
        text=get_text("en", "buttons.english"), 
        callback_data="lang_en"
    ))
    builder.add(InlineKeyboardButton(
        text=get_text("uk", "buttons.back"), 
        callback_data="back_to_main"
    ))
    
    builder.adjust(1)  # 1 кнопка в ряд
    return builder.as_markup()

def get_buckshot_menu_keyboard(locale: str = "uk") -> InlineKeyboardMarkup:
    """Меню для Buckshot Roulette"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text=get_text(locale, "buttons.test_mode"), 
        callback_data="buckshot_test"
    ))
    builder.add(InlineKeyboardButton(
        text=get_text(locale, "buttons.real_mode"), 
        callback_data="buckshot_real"
    ))
    builder.add(InlineKeyboardButton(
        text=get_text(locale, "buttons.rules"), 
        callback_data="rules_buckshot"
    ))
    builder.add(InlineKeyboardButton(
        text=get_text(locale, "buttons.back"), 
        callback_data="back_to_main"
    ))
    
    builder.adjust(2)
    return builder.as_markup()

def get_blackjack_menu_keyboard(locale: str = "uk") -> InlineKeyboardMarkup:
    """Меню для BlackJack"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text=get_text(locale, "buttons.test_mode"), 
        callback_data="blackjack_create_test"
    ))
    builder.add(InlineKeyboardButton(
        text=get_text(locale, "buttons.real_mode"), 
        callback_data="blackjack_create_real"
    ))
    builder.add(InlineKeyboardButton(
        text=get_text(locale, "buttons.rules"), 
        callback_data="rules_blackjack"
    ))
    builder.add(InlineKeyboardButton(
        text=get_text(locale, "buttons.back"), 
        callback_data="back_to_main"
    ))
    
    builder.adjust(2)
    return builder.as_markup()

def get_back_keyboard(locale: str = "uk") -> InlineKeyboardMarkup:
    """Кнопка назад"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text=get_text(locale, "buttons.back"), 
        callback_data="back_to_main"
    ))
    return builder.as_markup()

def get_webapp_keyboard(url: str, text: str = None, locale: str = "uk") -> InlineKeyboardMarkup:
    """Клавіатура з WebApp кнопкою"""
    if text is None:
        text = get_text(locale, "buttons.open_game")
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text=text,
        web_app={"url": url}
    ))
    builder.add(InlineKeyboardButton(
        text=get_text(locale, "buttons.back"), 
        callback_data="back_to_main"
    ))
    return builder.as_markup() 