# 🎮 Unified Games Bot

Об'єднаний Telegram бот для двох ігор: **Buckshot Roulette** та **BlackJack**.

## 🎯 Особливості

- **Два режими гри**: Тестовий та реальні гроші
- **WebApp інтеграція**: Грайте прямо в Telegram
- **Зручне меню**: Легкий вибір гри та режиму
- **Детальні правила**: Вбудована довідка по кожній грі

## 🎮 Доступні ігри

### 🎰 Buckshot Roulette
- Гра на виживання з рушницею
- 6 патронів (живі та холості)
- Стратегія та психологія

### 🃏 BlackJack
- Класична карткова гра
- Гра проти гравця або дилера
- Підтримка реальних грошей

## 🚀 Встановлення

1. **Клонуйте репозиторій:**
```bash
git clone <repository-url>
cd unified-games-bot
```

2. **Встановіть залежності:**
```bash
pip install -r requirements.txt
```

3. **Налаштуйте конфігурацію:**
```bash
cp env.example .env
# Відредагуйте .env файл з вашими налаштуваннями
```

4. **Налаштуйте змінні середовища в .env:**
```env
BOT_TOKEN=your_telegram_bot_token
BLACKJACK_WEBAPP_URL=https://your-blackjack-domain.com
BLACKJACK_FLASK_API_URL=http://localhost:5000
BUCKSHOT_WEBAPP_URL=http://localhost:3000
```

## 🏃‍♂️ Запуск

### Polling режим (для розробки):
```bash
python main.py
```

### Webhook режим (для продакшену):
```bash
python run_webhook.py
```

## ⚙️ Налаштування

### Для BlackJack:
1. Запустіть Flask сервер з `cards-main` директорії
2. Налаштуйте `BLACKJACK_FLASK_API_URL` та `BLACKJACK_WEBAPP_URL`

### Для Buckshot Roulette:
1. Запустіть React додаток з `buckshot-roulette` директорії
2. Налаштуйте `BUCKSHOT_WEBAPP_URL`

## 📱 Використання

1. **Запустіть бота** командою `/start`
2. **Оберіть гру** з головного меню
3. **Виберіть режим**: тестовий або реальні гроші
4. **Натисніть кнопку** для відкриття WebApp
5. **Грайте** прямо в Telegram!

## 🛠️ Структура проекту

```
unified-games-bot/
├── main.py              # Головний файл бота (polling)
├── run_webhook.py       # Webhook версія
├── config.py            # Конфігурація
├── handlers.py          # Обробники команд
├── keyboards.py         # Клавіатури
├── requirements.txt     # Залежності
├── env.example          # Приклад конфігурації
└── README.md           # Цей файл
```

## 🔧 API Endpoints

### BlackJack API:
- `POST /api/sessions/create` - Створити нову сесію
- `POST /api/sessions/{chat_id}/join` - Приєднатися до сесії

### Buckshot Roulette:
- WebApp доступ через налаштований URL

## 📋 Команди бота

- `/start` - Головне меню
- `/help` - Довідка
- `/rules` - Правила ігор

## 🐛 Виправлення проблем

### Помилка з'єднання з BlackJack API:
- Перевірте, чи запущений Flask сервер
- Перевірте `BLACKJACK_FLASK_API_URL` в конфігурації

### WebApp не відкривається:
- Перевірте URL в конфігурації
- Переконайтеся, що сервер доступний

### Помилка токена:
- Перевірте `BOT_TOKEN` в .env файлі
- Переконайтеся, що токен валідний

## 📄 Ліцензія

Цей проект розроблений для освітніх цілей.

## 🤝 Підтримка

Якщо у вас є питання або проблеми, створіть issue в репозиторії. 