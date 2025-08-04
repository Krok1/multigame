import logging
import requests
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import config
from keyboards import (
    get_main_menu_keyboard,
    get_buckshot_menu_keyboard,
    get_blackjack_menu_keyboard,
    get_back_keyboard,
    get_webapp_keyboard,
    get_language_keyboard
)
from localization import get_text
from models import get_user_language, create_or_update_user, update_user_language

logger = logging.getLogger(__name__)
router = Router()

class GameStates(StatesGroup):
    """Стани для гри"""
    selecting_game = State()
    selecting_mode = State()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обробник команди /start"""
    # Створити або оновити користувача
    from models import SessionLocal
    db = SessionLocal()
    try:
        user = create_or_update_user(
            db, 
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
            message.from_user.last_name
        )
        locale = user.language
    finally:
        db.close()
    
    await message.answer(
        get_text(locale, "bot.welcome"),
        reply_markup=get_main_menu_keyboard(locale)
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обробник команди /help"""
    await show_help(message)

@router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    """Показати допомогу"""
    locale = get_user_language(None, callback.from_user.id)
    help_text = get_text(locale, "bot.help")
    
    await callback.message.edit_text(help_text, reply_markup=get_back_keyboard(locale))
    await callback.answer()

@router.callback_query(F.data == "rules")
async def show_rules(callback: CallbackQuery):
    """Показати загальні правила"""
    locale = get_user_language(None, callback.from_user.id)
    rules_text = get_text(locale, "bot.rules")
    
    await callback.message.edit_text(rules_text, reply_markup=get_back_keyboard(locale))
    await callback.answer()

@router.callback_query(F.data == "game_buckshot")
async def buckshot_menu(callback: CallbackQuery):
    """Меню Buckshot Roulette"""
    locale = get_user_language(None, callback.from_user.id)
    await callback.message.edit_text(
        get_text(locale, "games.buckshot.name") + "\n\n" + get_text(locale, "games.buckshot.description"),
        reply_markup=get_buckshot_menu_keyboard(locale)
    )
    await callback.answer()

@router.callback_query(F.data == "game_blackjack")
async def blackjack_menu(callback: CallbackQuery):
    """Меню BlackJack"""
    locale = get_user_language(None, callback.from_user.id)
    await callback.message.edit_text(
        get_text(locale, "games.blackjack.name") + "\n\n" + get_text(locale, "games.blackjack.description"),
        reply_markup=get_blackjack_menu_keyboard(locale)
    )
    await callback.answer()

@router.callback_query(F.data == "rules_buckshot")
async def buckshot_rules(callback: CallbackQuery):
    """Правила Buckshot Roulette"""
    locale = get_user_language(None, callback.from_user.id)
    rules_text = get_text(locale, "games.buckshot.rules")
    
    await callback.message.edit_text(rules_text, reply_markup=get_back_keyboard(locale))
    await callback.answer()

@router.callback_query(F.data == "rules_blackjack")
async def blackjack_rules(callback: CallbackQuery):
    """Правила BlackJack"""
    locale = get_user_language(None, callback.from_user.id)
    rules_text = get_text(locale, "games.blackjack.rules")
    
    await callback.message.edit_text(rules_text, reply_markup=get_back_keyboard(locale))
    await callback.answer()

@router.callback_query(F.data.startswith("buckshot_"))
async def handle_buckshot_game(callback: CallbackQuery):
    """Обробник Buckshot Roulette"""
    game_mode = callback.data.split("_")[1]  # test або real
    
    try:
        # Створюємо сесію через Buckshot API
        import random
        chat_id = random.randint(100000, 999999)
        
        session_data = {
            "user_id": callback.from_user.id,
            "username": callback.from_user.username or callback.from_user.first_name,
            "mode": game_mode,
            "chat_id": chat_id,
            "stake": 10.0
        }
        
        response = requests.post(
            f"{config.BUCKSHOT_API_URL}/api/sessions",
            json=session_data,
            headers={
                "bypass-tunnel-reminder": "true"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            chat_id = data.get("session", {}).get("chat_id")
            
            webapp_url = f"{config.BUCKSHOT_WEBAPP_URL}?chat_id={chat_id}&mode={game_mode}"
            
            locale = get_user_language(None, callback.from_user.id)
            
            if game_mode == "test":
                message_text = get_text(locale, "games.buckshot.session_created", chat_id=chat_id)
            else:
                message_text = get_text(locale, "games.buckshot.session_created_real", chat_id=chat_id)
            
            # Створюємо клавіатуру з кнопками
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(
                text=get_text(locale, "buttons.open_game"),
                web_app={"url": webapp_url}
            ))
            builder.add(InlineKeyboardButton(
                text=get_text(locale, "buttons.invite_player"),
                callback_data=f"invite_buckshot_{chat_id}"
            ))
            builder.add(InlineKeyboardButton(
                text=get_text(locale, "buttons.back"),
                callback_data="back_to_main"
            ))
            builder.adjust(1)
            
            await callback.message.edit_text(
                message_text,
                reply_markup=builder.as_markup()
            )
        else:
            locale = get_user_language(None, callback.from_user.id)
            await callback.message.edit_text(
                get_text(locale, "errors.session_creation_failed"),
                reply_markup=get_back_keyboard(locale)
            )
    
    except Exception as e:
        logger.error(f"Error creating Buckshot session: {e}")
        locale = get_user_language(None, callback.from_user.id)
        await callback.message.edit_text(
            get_text(locale, "errors.connection_failed"),
            reply_markup=get_back_keyboard(locale)
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("blackjack_create_"))
async def handle_blackjack_create(callback: CallbackQuery):
    """Створити гру BlackJack"""
    game_mode = callback.data.split("_")[2]  # test або real
    
    try:
        # Створюємо сесію через Flask API
        # Генеруємо унікальний chat_id
        import random
        chat_id = random.randint(100000, 999999)
        
        session_data = {
            "user_id": callback.from_user.id,
            "username": callback.from_user.username or callback.from_user.first_name,
            "mode": game_mode,
            "chat_id": chat_id,
            "stake": 10.0  # Ставка за замовчуванням
        }
        
        response = requests.post(
            f"{config.BLACKJACK_FLASK_API_URL}/api/sessions",
            json=session_data,
            headers={
                "bypass-tunnel-reminder": "true",
                "ngrok-skip-browser-warning": "1"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            chat_id = data.get("session", {}).get("chat_id")
            
            webapp_url = f"{config.BLACKJACK_WEBAPP_URL}/webapp?chat_id={chat_id}"
            
            if game_mode == "test":
                message_text = (
                    "🃏 <b>BlackJack - Тестовий режим</b>\n\n"
                    f"🎮 ID гри: <code>{chat_id}</code>\n"
                    "Натисніть кнопку нижче, щоб відкрити гру:"
                )
            else:
                message_text = (
                    "🃏 <b>BlackJack - Реальні гроші</b>\n\n"
                    f"🎮 ID гри: <code>{chat_id}</code>\n"
                    "Натисніть кнопку нижче, щоб відкрити гру:"
                )
            
            # Створюємо клавіатуру з двома кнопками
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(
                text="🎮 Відкрити BlackJack",
                web_app={"url": webapp_url}
            ))
            builder.add(InlineKeyboardButton(
                text="👥 Запросити гравця",
                callback_data=f"invite_player_{chat_id}"
            ))
            builder.add(InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="back_to_main"
            ))
            builder.adjust(1)  # По одній кнопці в ряд
            
            await callback.message.edit_text(
                message_text,
                reply_markup=builder.as_markup()
            )
        else:
            await callback.message.edit_text(
                "❌ Помилка створення гри. Спробуйте ще раз.",
                reply_markup=get_back_keyboard()
            )
    
    except Exception as e:
        logger.error(f"Error creating BlackJack session: {e}")
        await callback.message.edit_text(
            "❌ Помилка з'єднання з сервером. Спробуйте ще раз.",
            reply_markup=get_back_keyboard()
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("invite_player_"))
async def invite_player(callback: CallbackQuery):
    """Запросити гравця до гри BlackJack"""
    chat_id = callback.data.split("_")[2]
    
    # Створюємо повідомлення для пересилання
    invite_text = (
        f"🎮 <b>Запрошення до гри BlackJack!</b>\n\n"
        f"🎯 ID гри: <code>{chat_id}</code>\n"
        f"👤 Запрошує: {callback.from_user.first_name}\n\n"
        f"🎲 Щоб приєднатися до гри:\n"
        f"1. Натисніть кнопку нижче\n"
        f"2. Або відправте: <code>/join {chat_id}</code>\n\n"
        f"🃏 Гратимуть: 2 гравці\n"
        f"💰 Ставка: 10 монет (тестовий режим)"
    )
    
    # Створюємо клавіатуру з кнопкою приєднання
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="🎮 Приєднатися до гри",
        callback_data=f"join_game_{chat_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="❌ Відхилити",
        callback_data="decline_invite"
    ))
    builder.adjust(1)
    
    await callback.message.edit_text(
        invite_text,
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("invite_buckshot_"))
async def invite_buckshot_player(callback: CallbackQuery):
    """Запросити гравця до гри Buckshot Roulette"""
    chat_id = callback.data.split("_")[2]
    locale = get_user_language(None, callback.from_user.id)
    
    # Створюємо повідомлення для пересилання
    invite_text = get_text(locale, "games.buckshot.invite_text", 
                          chat_id=chat_id, creator_name=callback.from_user.first_name)
    
    # Створюємо клавіатуру з кнопкою приєднання
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text=get_text(locale, "buttons.join_game"),
        callback_data=f"join_buckshot_{chat_id}"
    ))
    builder.add(InlineKeyboardButton(
        text=get_text(locale, "buttons.decline"),
        callback_data="decline_invite"
    ))
    builder.adjust(1)
    
    await callback.message.edit_text(
        invite_text,
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("join_game_"))
async def join_game(callback: CallbackQuery):
    """Приєднатися до гри"""
    chat_id = callback.data.split("_")[2]
    
    try:
        # Приєднуємося до гри через API
        join_data = {
            "user_id": callback.from_user.id,
            "username": callback.from_user.username or callback.from_user.first_name
        }
        
        response = requests.post(
            f"{config.BLACKJACK_FLASK_API_URL}/api/sessions/{chat_id}/join",
            json=join_data,
            headers={
                "bypass-tunnel-reminder": "true",
                "ngrok-skip-browser-warning": "1"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            webapp_url = f"{config.BLACKJACK_WEBAPP_URL}/webapp?chat_id={chat_id}"
            
            await callback.message.edit_text(
                f"✅ <b>Ви приєдналися до гри!</b>\n\n"
                f"🎮 ID гри: <code>{chat_id}</code>\n"
                f"👥 Гравець 1: {data.get('player1_username', 'Невідомо')}\n"
                f"👤 Гравець 2: {callback.from_user.first_name}\n\n"
                f"🎲 Натисніть кнопку нижче, щоб почати гру:",
                reply_markup=get_webapp_keyboard(webapp_url, "🎮 Почати гру")
            )
        else:
            await callback.message.edit_text(
                "❌ Помилка приєднання до гри. Можливо гра вже заповнена або не існує.",
                reply_markup=get_back_keyboard()
            )
    
    except Exception as e:
        logger.error(f"Error joining game: {e}")
        await callback.message.edit_text(
            "❌ Помилка з'єднання з сервером. Спробуйте ще раз.",
            reply_markup=get_back_keyboard()
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("join_buckshot_"))
async def join_buckshot_game(callback: CallbackQuery):
    """Приєднатися до гри Buckshot Roulette"""
    chat_id = callback.data.split("_")[2]
    
    try:
        # Приєднуємося до гри через Buckshot API
        session_data = {
            "user_id": callback.from_user.id,
            "username": callback.from_user.username or callback.from_user.first_name
        }
        
        response = requests.post(
            f"{config.BUCKSHOT_API_URL}/api/sessions/{chat_id}/join",
            json=session_data,
            headers={
                "bypass-tunnel-reminder": "true"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            webapp_url = f"{config.BUCKSHOT_WEBAPP_URL}?chat_id={chat_id}&mode=test"
            locale = get_user_language(None, callback.from_user.id)
            
            message_text = get_text(locale, "games.buckshot.joined", 
                                  chat_id=chat_id, player_name=callback.from_user.first_name)
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(
                text=get_text(locale, "buttons.open_game"),
                web_app={"url": webapp_url}
            ))
            builder.add(InlineKeyboardButton(
                text=get_text(locale, "buttons.back"),
                callback_data="back_to_main"
            ))
            builder.adjust(1)
            
            await callback.message.edit_text(
                message_text,
                reply_markup=builder.as_markup()
            )
        else:
            locale = get_user_language(None, callback.from_user.id)
            await callback.message.edit_text(
                get_text(locale, "errors.join_failed"),
                reply_markup=get_back_keyboard(locale)
            )
    
    except Exception as e:
        logger.error(f"Error joining Buckshot game: {e}")
        locale = get_user_language(None, callback.from_user.id)
        await callback.message.edit_text(
            get_text(locale, "errors.connection_failed"),
            reply_markup=get_back_keyboard(locale)
        )
    
    await callback.answer()

@router.callback_query(F.data == "decline_invite")
async def decline_invite(callback: CallbackQuery):
    """Відхилити запрошення"""
    locale = get_user_language(None, callback.from_user.id)
    await callback.message.edit_text(
        get_text(locale, "buttons.decline"),
        reply_markup=get_back_keyboard(locale)
    )
    await callback.answer()

@router.callback_query(F.data == "language")
async def language_menu(callback: CallbackQuery):
    """Меню вибору мови"""
    locale = get_user_language(None, callback.from_user.id)
    await callback.message.edit_text(
        get_text(locale, "bot.select_language"),
        reply_markup=get_language_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("lang_"))
async def change_language(callback: CallbackQuery):
    """Змінити мову користувача"""
    new_language = callback.data.split("_")[1]  # uk, ru, en
    
    # Оновити мову в базі даних
    from models import SessionLocal
    db = SessionLocal()
    try:
        success = update_user_language(db, callback.from_user.id, new_language)
        if success:
            await callback.message.edit_text(
                get_text(new_language, "bot.language_changed"),
                reply_markup=get_main_menu_keyboard(new_language)
            )
        else:
            await callback.message.edit_text(
                "❌ Помилка зміни мови",
                reply_markup=get_main_menu_keyboard()
            )
    finally:
        db.close()
    
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery):
    """Повернутися до головного меню"""
    locale = get_user_language(None, callback.from_user.id)
    await callback.message.edit_text(
        get_text(locale, "bot.welcome"),
        reply_markup=get_main_menu_keyboard(locale)
    )
    await callback.answer()

@router.message(Command("join"))
async def cmd_join(message: Message):
    """Команда для приєднання до гри"""
    if not message.text or len(message.text.split()) < 2:
        await message.answer(
            "❌ Неправильний формат команди.\n\n"
            "Використовуйте: <code>/join ID_гри</code>\n"
            "Наприклад: <code>/join 123456</code>"
        )
        return
    
    try:
        chat_id = int(message.text.split()[1])
    except ValueError:
        await message.answer(
            "❌ ID гри має бути числом.\n\n"
            "Використовуйте: <code>/join ID_гри</code>\n"
            "Наприклад: <code>/join 123456</code>"
        )
        return
    
    try:
        # Приєднуємося до гри через API
        join_data = {
            "user_id": message.from_user.id,
            "username": message.from_user.username or message.from_user.first_name
        }
        
        response = requests.post(
            f"{config.BLACKJACK_FLASK_API_URL}/api/sessions/{chat_id}/join",
            json=join_data,
            headers={
                "bypass-tunnel-reminder": "true",
                "ngrok-skip-browser-warning": "1"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            webapp_url = f"{config.BLACKJACK_WEBAPP_URL}/webapp?chat_id={chat_id}"
            
            await message.answer(
                f"✅ <b>Ви приєдналися до гри!</b>\n\n"
                f"🎮 ID гри: <code>{chat_id}</code>\n"
                f"👥 Гравець 1: {data.get('player1_username', 'Невідомо')}\n"
                f"👤 Гравець 2: {message.from_user.first_name}\n\n"
                f"🎲 Натисніть кнопку нижче, щоб почати гру:",
                reply_markup=get_webapp_keyboard(webapp_url, "🎮 Почати гру")
            )
        else:
            error_data = response.json()
            error_msg = error_data.get('error', 'Невідома помилка')
            await message.answer(
                f"❌ Помилка приєднання до гри: {error_msg}\n\n"
                "Можливо гра вже заповнена або не існує."
            )
    
    except Exception as e:
        logger.error(f"Error joining game: {e}")
        await message.answer(
            "❌ Помилка з'єднання з сервером. Спробуйте ще раз."
        )

@router.message()
async def handle_unknown_message(message: Message):
    """Обробник невідомих повідомлень"""
    locale = get_user_language(None, message.from_user.id)
    await message.answer(
        get_text(locale, "bot.unknown_message")
    ) 