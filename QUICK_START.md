# ⚡ Швидкий старт

## 🎯 Що це?
Платформа з трьома іграми:
- **Buckshot Roulette** - гра в рулетку з дробовиком
- **Blackjack** - класична гра в 21
- **Telegram Bot** - бот для гри в обидві ігри

## 🚀 Швидкий запуск (1 хвилина)

### Вимоги
- Python 3.8+
- Node.js 16+
- npm

### Кроки:

1. **Встановіть залежності:**
```bash
# Buckshot Roulette
cd buckshot-roulette
npm install
cd python && pip install -r requirements.txt && cd ../..

# Blackjack
cd cards-main
pip install -r requirements.txt
cd ..

# Telegram Bot (опціонально)
cd unified-games-bot
pip install -r requirements.txt
cp env.example .env
# Відредагуйте .env з вашим токеном бота
cd ..
```

2. **Запустіть всі сервіси:**
```bash
./start_all.sh
```

3. **Відкрийте браузер:**
- Buckshot Roulette: http://localhost:5173
- Blackjack: http://localhost:5000

## 🛑 Зупинка
```bash
./stop_all.sh
```

## 📱 Telegram Bot
Якщо налаштували бота:
1. Знайдіть свого бота в Telegram
2. Відправте `/start`
3. Виберіть гру

## 🔧 Ручний запуск

### Buckshot Roulette
```bash
cd buckshot-roulette
npm run dev          # Frontend
cd python
python buckshot_api.py  # Backend
```

### Blackjack
```bash
cd cards-main
python app.py
```

### Telegram Bot
```bash
cd unified-games-bot
python main.py
```

## ❓ Проблеми?

### Порт зайнятий?
- Зупиніть сервіси: `./stop_all.sh`
- Перезапустіть: `./start_all.sh`

### Помилки встановлення?
- Перевірте версії Python/Node.js
- Спробуйте: `pip install --upgrade pip`

### Telegram Bot не працює?
- Перевірте токен в `.env` файлі
- Переконайтеся що бот активний

## 📞 Підтримка
Створіть issue в репозиторії або зверніться до документації в `README.md` 