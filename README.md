# 🎮 Multi-Game Platform

Цей проект містить три різні ігри з можливістю мультиплеєру та інтеграцією з Telegram ботом.

## 📁 Структура проекту

```
final/
├── buckshot-roulette/     # Гра Buckshot Roulette (React + TypeScript)
├── cards-main/           # Гра Blackjack (Flask + JavaScript)
└── unified-games-bot/    # Telegram бот для всіх ігор
```

## 🎯 Доступні ігри

### 1. Buckshot Roulette
- **Технології**: React, TypeScript, Tailwind CSS, Vite
- **Опис**: Гра в рулетку з дробовиком
- **Можливості**: Одиночна гра, мультиплеєр
- **API**: Python Flask backend

### 2. Blackjack (21)
- **Технології**: Flask, JavaScript, HTML/CSS
- **Опис**: Класична гра в 21
- **Можливості**: Одиночна гра, мультиплеєр
- **API**: Python Flask backend

### 3. Telegram Bot
- **Технології**: Python, python-telegram-bot
- **Опис**: Бот для гри в обидві ігри через Telegram
- **Можливості**: Мультимовність (EN, RU, UK), вебхуки

## 🚀 Швидкий старт

### Вимоги
- Python 3.8+
- Node.js 16+
- npm або yarn

### Встановлення та запуск

#### 1. Buckshot Roulette
```bash
cd buckshot-roulette

# Встановлення залежностей
npm install

# Запуск frontend
npm run dev

# В окремому терміналі - запуск backend
cd python
pip install -r requirements.txt
python buckshot_api.py
```

#### 2. Blackjack
```bash
cd cards-main

# Встановлення залежностей
pip install -r requirements.txt

# Запуск гри
python app.py
```

#### 3. Telegram Bot
```bash
cd unified-games-bot

# Встановлення залежностей
pip install -r requirements.txt

# Налаштування змінних середовища
cp env.example .env
# Відредагуйте .env файл з вашими токенами

# Запуск бота
python main.py
```

## 🌐 Доступ до ігор

- **Buckshot Roulette**: http://localhost:5173
- **Blackjack**: http://localhost:5000
- **Telegram Bot**: Після налаштування вебхуків

## 📝 Налаштування Telegram Bot

1. Створіть бота через @BotFather
2. Скопіюйте токен в `.env` файл
3. Налаштуйте вебхуки або використовуйте polling
4. Запустіть бота

## 🔧 Розробка

### Структура файлів

#### Buckshot Roulette
- `src/` - React компоненти
- `public/` - Статичні файли
- `python/` - Flask API
- `package.json` - Node.js залежності

#### Blackjack
- `templates/` - HTML шаблони
- `static/` - CSS/JS файли
- `app.py` - Основний Flask додаток
- `bot.py` - Telegram бот для цієї гри

#### Unified Games Bot
- `locales/` - Файли локалізації
- `logs/` - Логи
- `main.py` - Основний файл бота
- `handlers.py` - Обробники команд

## 📄 Ліцензія

**MIT License with Commercial Use Restriction**

Цей проект доступний для особистого та навчального використання безкоштовно.

**Для комерційного використання потрібен письмовий дозвіл автора.**

Детальніше дивіться файли:
- [LICENSE](LICENSE) - повна ліцензія
- [COMMERCIAL_USE.md](COMMERCIAL_USE.md) - інформація про комерційне використання

### 📞 Контакти для комерційної ліцензії:
- **Автор**: Artur
- **Email**: [ВКАЖІТЬ ВАШУ ПОШТУ]
- **GitHub**: [ВКАЖІТЬ ВАШ GITHUB]
- **Telegram**: [ВКАЖІТЬ ВАШ TELEGRAM]

## 🤝 Внесок

Вітаються pull requests та issues для некомерційних цілей!

## 📞 Підтримка

Якщо у вас виникли питання:
- Для технічних проблем: створіть issue в репозиторії
- Для комерційного використання: зверніться до автора 