from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Tuple

def get_start_keyboard() -> InlineKeyboardMarkup:
    """Get start game keyboard"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="🎮 Start Game",
        callback_data="start_game"
    ))
    builder.add(InlineKeyboardButton(
        text="📖 Rules",
        callback_data="rules"
    ))
    builder.add(InlineKeyboardButton(
        text="🌐 Play Web Version",
        web_app=WebAppInfo(url="https://1aeb8bd19a04.ngrok-free.app")
    ))
    builder.adjust(1)
    return builder.as_markup()

def get_game_keyboard() -> InlineKeyboardMarkup:
    """Get main game action keyboard"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="🔫 Shoot Self",
        callback_data="shoot_self"
    ))
    builder.add(InlineKeyboardButton(
        text="🔫 Shoot Opponent", 
        callback_data="shoot_opponent"
    ))
    builder.add(InlineKeyboardButton(
        text="🎒 Use Items",
        callback_data="show_bonuses"
    ))
    builder.add(InlineKeyboardButton(
        text="📊 Status",
        callback_data="status"
    ))
    builder.add(InlineKeyboardButton(
        text="❌ End Game",
        callback_data="end_game"
    ))
    builder.adjust(2, 1, 2)
    return builder.as_markup()

def get_bonuses_keyboard(bonuses: List[Tuple[int, str, bool]]) -> InlineKeyboardMarkup:
    """Get bonuses selection keyboard"""
    builder = InlineKeyboardBuilder()
    
    for index, description, used in bonuses:
        if not used:
            builder.add(InlineKeyboardButton(
                text=description,
                callback_data=f"use_bonus_{index}"
            ))
        else:
            builder.add(InlineKeyboardButton(
                text=f"❌ {description}",
                callback_data="used_bonus"
            ))
    
    builder.add(InlineKeyboardButton(
        text="🔙 Back to Game",
        callback_data="back_to_game"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

def get_confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    """Get confirmation keyboard"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="✅ Yes",
        callback_data=f"confirm_{action}"
    ))
    builder.add(InlineKeyboardButton(
        text="❌ No",
        callback_data="back_to_game"
    ))
    builder.adjust(2)
    return builder.as_markup()

def get_game_over_keyboard() -> InlineKeyboardMarkup:
    """Get game over keyboard"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="🔄 Play Again",
        callback_data="start_game"
    ))
    builder.add(InlineKeyboardButton(
        text="📊 Final Status",
        callback_data="status"
    ))
    builder.adjust(2)
    return builder.as_markup()