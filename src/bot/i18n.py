"""Bot UI translations. All keys must exist in 'en'; other langs fall back to 'en'."""

STRINGS = {
    "en": {
        "welcome": (
            "👋 Welcome {name}!\n\n"
            "This bot monitors appointment availability for Düsseldorf city services.\n\n"
            "Commands:\n"
            "/subscribe — Subscribe to a service\n"
            "/list — View your subscriptions\n"
            "/unsubscribe — Cancel a subscription\n"
            "/check — Manual check\n"
            "/language — Change language\n"
            "/help — Help\n\n"
            "Your plan: {plan}"
        ),
        "help_text": (
            "📖 *Help & Commands*\n\n"
            "/start — Start the bot\n"
            "/subscribe — Subscribe to appointment notifications\n"
            "/list — View your active subscriptions\n"
            "/unsubscribe — Cancel a subscription\n"
            "/check — Manually check for appointments\n"
            "/language — Change bot language\n"
            "/help — This message\n\n"
            "*How it works:*\n"
            "1. Subscribe to a service via /subscribe\n"
            "2. Bot checks automatically and notifies you when slots open\n"
            "3. Manage subscriptions with /list and /unsubscribe\n\n"
            "*Plans:*\n"
            "• FREE: Up to 3 subscriptions, checks every 12 hours\n"
            "• PREMIUM: Unlimited subscriptions, custom schedule"
        ),
        "user_not_found": "❌ User not found. Please use /start first.",
        "no_subs": "📭 You have no active subscriptions.\n\nUse /subscribe to start monitoring a service.",
        "no_subs_short": "📭 You have no active subscriptions.",
        "subs_header": "📋 *Your Active Subscriptions:*\n\n",
        "interval_label": "Every {n}h",
        "last_check_label": "Last check: {time}",
        "never": "Never",
        "btn_unsub_prefix": "❌ Unsubscribe: ",
        "no_services": "❌ No services available at the moment.",
        "no_services_short": "❌ No services available.",
        "select_dept": "📝 *Select a department:*",
        "select_unsub": "🗑️ *Select subscription to cancel:*",
        "select_check": "🔍 *Select subscription to check:*",
        "cancelled": "❌ Cancelled.",
        "btn_cancel": "❌ Cancel",
        "btn_back": "⬅️ Back",
        "dept_not_found": "❌ Department not found.",
        "no_services_dept": "❌ No services found in this department.",
        "select_cat": "Select a category:",
        "cat_not_found": "❌ Category not found.",
        "no_services_cat": "❌ No services found.",
        "select_service": "Select a service:",
        "user_not_found_short": "❌ User not found.",
        "plan_limit": "❌ Free plan allows up to 3 subscriptions.\n\nUse /premium to upgrade.",
        "subscribed": "✅ *Subscribed!*\n\nService: {name}\nChecks: {freq}\n\nRunning first check now...",
        "freq_twice_daily": "twice daily",
        "freq_four_daily": "4× daily (in peak windows)",
        "freq_every_15min": "Every 15 min",
        "freq_every_nh": "every {n}h",
        "already_subscribed": "❌ Already subscribed to this service.",
        "unsub_success": "✅ Subscription cancelled.",
        "unsub_fail": "❌ Failed to cancel subscription.",
        "check_fail": "❌ Failed to run check.",
        "found_apts_header": "✅ *Found {n} appointment(s)!*\n\n",
        "apt_at": "at",
        "more_apts": "\n…and {n} more",
        "no_apts": (
            "❌ No appointments available right now.\n\n"
            "The bot will notify you when slots open up."
        ),
        "check_error": "❌ Error: {msg}",
        "checking": "🔍 Checking for appointments… Please wait.",
        "premium_unavailable": "🚧 Premium subscriptions are temporarily unavailable (coming soon). Check back soon!",
        "use_start": "❌ Please use /start first.",
        "already_premium": "✅ You already have Premium!",
        "premium_no_user": "❌ Could not activate Premium — user not found.",
        "premium_activated": (
            "🎉 *Premium activated!*\n\nYou now have unlimited subscriptions.\n"
            "Use /setschedule <hours> to customize check frequency."
        ),
        "premium_only": "⚠️ Custom schedules are a Premium feature.\nUse /premium to upgrade.",
        "setschedule_usage": "Usage: /setschedule <hours>\nExample: /setschedule 2",
        "hours_invalid": "❌ Hours must be between 1 and 24.",
        "schedule_updated": "✅ All subscriptions will now check every {n}h.",
        "language_choose": "🌐 *Choose your language:*",
        "language_set": "✅ Language updated.",
        "ad_premium_upsell": (
            "⭐ Free: 4 checks/day. Premium: every 15 min — always first, never miss a slot. /premium"
        ),
        "btn_get_premium": "⭐ Get Premium (coming soon)",
        "terms_intro": "📋 *Terms of Use*",
    },
    "de": {
        "welcome": (
            "👋 Willkommen, {name}!\n\n"
            "Dieser Bot überwacht Terminverfügbarkeiten bei Düsseldorfer Stadtdiensten.\n\n"
            "Befehle:\n"
            "/subscribe — Service abonnieren\n"
            "/list — Abonnements anzeigen\n"
            "/unsubscribe — Abonnement kündigen\n"
            "/check — Manuelle Prüfung\n"
            "/language — Sprache ändern\n"
            "/help — Hilfe\n\n"
            "Ihr Plan: {plan}"
        ),
        "help_text": (
            "📖 *Hilfe & Befehle*\n\n"
            "/start — Bot starten\n"
            "/subscribe — Terminbenachrichtigungen abonnieren\n"
            "/list — Aktive Abonnements anzeigen\n"
            "/unsubscribe — Abonnement kündigen\n"
            "/check — Manuell nach Terminen suchen\n"
            "/language — Botsprache ändern\n"
            "/help — Diese Nachricht\n\n"
            "*So funktioniert es:*\n"
            "1. Abonnieren Sie einen Dienst über /subscribe\n"
            "2. Der Bot prüft automatisch und benachrichtigt Sie, wenn Termine frei werden\n"
            "3. Abonnements mit /list und /unsubscribe verwalten\n\n"
            "*Tarife:*\n"
            "• KOSTENLOS: Bis zu 3 Abonnements, Prüfung alle 12 Stunden\n"
            "• PREMIUM: Unbegrenzte Abonnements, individueller Zeitplan"
        ),
        "user_not_found": "❌ Benutzer nicht gefunden. Bitte /start verwenden.",
        "no_subs": "📭 Sie haben keine aktiven Abonnements.\n\nMit /subscribe einen Dienst überwachen.",
        "no_subs_short": "📭 Keine aktiven Abonnements.",
        "subs_header": "📋 *Ihre aktiven Abonnements:*\n\n",
        "interval_label": "Alle {n}h",
        "last_check_label": "Letzte Prüfung: {time}",
        "never": "Nie",
        "btn_unsub_prefix": "❌ Kündigen: ",
        "no_services": "❌ Derzeit keine Dienste verfügbar.",
        "no_services_short": "❌ Keine Dienste verfügbar.",
        "select_dept": "📝 *Abteilung wählen:*",
        "select_unsub": "🗑️ *Abonnement zum Kündigen wählen:*",
        "select_check": "🔍 *Abonnement zur Prüfung wählen:*",
        "cancelled": "❌ Abgebrochen.",
        "btn_cancel": "❌ Abbrechen",
        "btn_back": "⬅️ Zurück",
        "dept_not_found": "❌ Abteilung nicht gefunden.",
        "no_services_dept": "❌ Keine Dienste in dieser Abteilung.",
        "select_cat": "Kategorie wählen:",
        "cat_not_found": "❌ Kategorie nicht gefunden.",
        "no_services_cat": "❌ Keine Dienste gefunden.",
        "select_service": "Dienst wählen:",
        "user_not_found_short": "❌ Benutzer nicht gefunden.",
        "plan_limit": "❌ Kostenloses Konto: max. 3 Abonnements.\n\nMit /premium upgraden.",
        "subscribed": "✅ *Abonniert!*\n\nDienst: {name}\nPrüfungen: {freq}\n\nErste Prüfung läuft...",
        "freq_twice_daily": "zweimal täglich",
        "freq_four_daily": "4× täglich (in Spitzenzeiten)",
        "freq_every_15min": "Alle 15 Min.",
        "freq_every_nh": "alle {n}h",
        "already_subscribed": "❌ Bereits abonniert.",
        "unsub_success": "✅ Abonnement gekündigt.",
        "unsub_fail": "❌ Kündigung fehlgeschlagen.",
        "check_fail": "❌ Prüfung fehlgeschlagen.",
        "found_apts_header": "✅ *{n} Termin(e) gefunden!*\n\n",
        "apt_at": "um",
        "more_apts": "\n…und {n} weitere",
        "no_apts": (
            "❌ Derzeit keine Termine verfügbar.\n\n"
            "Sie werden benachrichtigt, wenn Termine frei werden."
        ),
        "check_error": "❌ Fehler: {msg}",
        "checking": "🔍 Termine werden geprüft… Bitte warten.",
        "premium_unavailable": "🚧 Premium-Abonnements sind vorübergehend nicht verfügbar (demnächst).",
        "use_start": "❌ Bitte zuerst /start verwenden.",
        "already_premium": "✅ Sie haben bereits Premium!",
        "premium_no_user": "❌ Premium konnte nicht aktiviert werden — Benutzer nicht gefunden.",
        "premium_activated": (
            "🎉 *Premium aktiviert!*\n\nUnbegrenzte Abonnements.\n"
            "Mit /setschedule <Stunden> den Zeitplan anpassen."
        ),
        "premium_only": "⚠️ Individuelle Zeitpläne sind ein Premium-Feature.\nMit /premium upgraden.",
        "setschedule_usage": "Verwendung: /setschedule <Stunden>\nBeispiel: /setschedule 2",
        "hours_invalid": "❌ Stunden müssen zwischen 1 und 24 liegen.",
        "schedule_updated": "✅ Alle Abonnements prüfen jetzt alle {n}h.",
        "language_choose": "🌐 *Sprache wählen:*",
        "language_set": "✅ Sprache gespeichert.",
        "ad_premium_upsell": (
            "⭐ Free: 4 Checks/Tag. Premium: alle 15 Min. — immer zuerst, kein Slot verpasst. /premium"
        ),
        "btn_get_premium": "⭐ Premium holen (demnächst)",
        "terms_intro": "📋 *Nutzungsbedingungen*",
    },
    "ru": {
        "welcome": (
            "👋 Добро пожаловать, {name}!\n\n"
            "Этот бот отслеживает доступность записи в службы города Дюссельдорф.\n\n"
            "Команды:\n"
            "/subscribe — Подписаться на услугу\n"
            "/list — Мои подписки\n"
            "/unsubscribe — Отменить подписку\n"
            "/check — Проверить вручную\n"
            "/language — Изменить язык\n"
            "/help — Помощь\n\n"
            "Ваш тариф: {plan}"
        ),
        "help_text": (
            "📖 *Помощь и команды*\n\n"
            "/start — Запустить бота\n"
            "/subscribe — Подписаться на уведомления о записи\n"
            "/list — Активные подписки\n"
            "/unsubscribe — Отменить подписку\n"
            "/check — Ручная проверка\n"
            "/language — Изменить язык\n"
            "/help — Это сообщение\n\n"
            "*Как это работает:*\n"
            "1. Подпишитесь на услугу через /subscribe\n"
            "2. Бот автоматически проверяет и уведомляет, когда появляются слоты\n"
            "3. Управляйте подписками через /list и /unsubscribe\n\n"
            "*Тарифы:*\n"
            "• БЕСПЛАТНО: до 3 подписок, проверка каждые 12 часов\n"
            "• PREMIUM: безлимитные подписки, настраиваемое расписание"
        ),
        "user_not_found": "❌ Пользователь не найден. Используйте /start.",
        "no_subs": "📭 У вас нет активных подписок.\n\nИспользуйте /subscribe для отслеживания.",
        "no_subs_short": "📭 Нет активных подписок.",
        "subs_header": "📋 *Ваши активные подписки:*\n\n",
        "interval_label": "Каждые {n}ч",
        "last_check_label": "Последняя проверка: {time}",
        "never": "Никогда",
        "btn_unsub_prefix": "❌ Отписаться: ",
        "no_services": "❌ Нет доступных услуг.",
        "no_services_short": "❌ Услуги недоступны.",
        "select_dept": "📝 *Выберите ведомство:*",
        "select_unsub": "🗑️ *Выберите подписку для отмены:*",
        "select_check": "🔍 *Выберите подписку для проверки:*",
        "cancelled": "❌ Отменено.",
        "btn_cancel": "❌ Отмена",
        "btn_back": "⬅️ Назад",
        "dept_not_found": "❌ Ведомство не найдено.",
        "no_services_dept": "❌ Услуги в этом ведомстве не найдены.",
        "select_cat": "Выберите категорию:",
        "cat_not_found": "❌ Категория не найдена.",
        "no_services_cat": "❌ Услуги не найдены.",
        "select_service": "Выберите услугу:",
        "user_not_found_short": "❌ Пользователь не найден.",
        "plan_limit": "❌ Бесплатный тариф: максимум 3 подписки.\n\nИспользуйте /premium для обновления.",
        "subscribed": "✅ *Подписка оформлена!*\n\nУслуга: {name}\nПроверки: {freq}\n\nЗапускаю первую проверку...",
        "freq_twice_daily": "дважды в день",
        "freq_four_daily": "4 раза в день (в часы пик)",
        "freq_every_15min": "Каждые 15 мин",
        "freq_every_nh": "каждые {n}ч",
        "already_subscribed": "❌ Уже подписаны на эту услугу.",
        "unsub_success": "✅ Подписка отменена.",
        "unsub_fail": "❌ Не удалось отменить подписку.",
        "check_fail": "❌ Не удалось выполнить проверку.",
        "found_apts_header": "✅ *Найдено {n} запис(ей)!*\n\n",
        "apt_at": "в",
        "more_apts": "\n…и ещё {n}",
        "no_apts": (
            "❌ Записи сейчас недоступны.\n\n"
            "Бот уведомит вас, когда появятся слоты."
        ),
        "check_error": "❌ Ошибка: {msg}",
        "checking": "🔍 Проверяю доступность… Подождите.",
        "premium_unavailable": "🚧 Premium-подписки временно недоступны (скоро).",
        "use_start": "❌ Сначала используйте /start.",
        "already_premium": "✅ У вас уже Premium!",
        "premium_no_user": "❌ Не удалось активировать Premium — пользователь не найден.",
        "premium_activated": (
            "🎉 *Premium активирован!*\n\nБезлимитные подписки.\n"
            "Используйте /setschedule <часы> для настройки расписания."
        ),
        "premium_only": "⚠️ Настраиваемое расписание — функция Premium.\nИспользуйте /premium.",
        "setschedule_usage": "Использование: /setschedule <часы>\nПример: /setschedule 2",
        "hours_invalid": "❌ Часы должны быть от 1 до 24.",
        "schedule_updated": "✅ Все подписки теперь проверяются каждые {n}ч.",
        "language_choose": "🌐 *Выберите язык:*",
        "language_set": "✅ Язык сохранён.",
        "ad_premium_upsell": (
            "⭐ Бесплатно: 4 проверки/день. Премиум: каждые 15 мин — всегда первым, ни один слот не пропущен. /premium"
        ),
        "btn_get_premium": "⭐ Получить Premium (скоро)",
    },
    "uk": {
        "welcome": (
            "👋 Вітаємо, {name}!\n\n"
            "Цей бот відстежує доступність запису до служб міста Дюссельдорф.\n\n"
            "Команди:\n"
            "/subscribe — Підписатися на послугу\n"
            "/list — Мої підписки\n"
            "/unsubscribe — Скасувати підписку\n"
            "/check — Перевірити вручну\n"
            "/language — Змінити мову\n"
            "/help — Допомога\n\n"
            "Ваш тариф: {plan}"
        ),
        "help_text": (
            "📖 *Допомога та команди*\n\n"
            "/start — Запустити бота\n"
            "/subscribe — Підписатися на сповіщення про запис\n"
            "/list — Активні підписки\n"
            "/unsubscribe — Скасувати підписку\n"
            "/check — Ручна перевірка\n"
            "/language — Змінити мову\n"
            "/help — Це повідомлення\n\n"
            "*Як це працює:*\n"
            "1. Підпишіться на послугу через /subscribe\n"
            "2. Бот автоматично перевіряє та сповіщає, коли з'являються слоти\n"
            "3. Керуйте підписками через /list та /unsubscribe\n\n"
            "*Тарифи:*\n"
            "• БЕЗКОШТОВНО: до 3 підписок, перевірка кожні 12 годин\n"
            "• PREMIUM: необмежені підписки, налаштований графік"
        ),
        "user_not_found": "❌ Користувача не знайдено. Використайте /start.",
        "no_subs": "📭 У вас немає активних підписок.\n\nВикористайте /subscribe для відстеження.",
        "no_subs_short": "📭 Немає активних підписок.",
        "subs_header": "📋 *Ваші активні підписки:*\n\n",
        "interval_label": "Кожні {n}г",
        "last_check_label": "Остання перевірка: {time}",
        "never": "Ніколи",
        "btn_unsub_prefix": "❌ Скасувати: ",
        "no_services": "❌ Немає доступних послуг.",
        "no_services_short": "❌ Послуги недоступні.",
        "select_dept": "📝 *Оберіть відомство:*",
        "select_unsub": "🗑️ *Оберіть підписку для скасування:*",
        "select_check": "🔍 *Оберіть підписку для перевірки:*",
        "cancelled": "❌ Скасовано.",
        "btn_cancel": "❌ Скасувати",
        "btn_back": "⬅️ Назад",
        "dept_not_found": "❌ Відомство не знайдено.",
        "no_services_dept": "❌ Послуги у цьому відомстві не знайдено.",
        "select_cat": "Оберіть категорію:",
        "cat_not_found": "❌ Категорію не знайдено.",
        "no_services_cat": "❌ Послуги не знайдено.",
        "select_service": "Оберіть послугу:",
        "user_not_found_short": "❌ Користувача не знайдено.",
        "plan_limit": "❌ Безкоштовний тариф: максимум 3 підписки.\n\nВикористайте /premium для оновлення.",
        "subscribed": "✅ *Підписку оформлено!*\n\nПослуга: {name}\nПеревірки: {freq}\n\nЗапускаю першу перевірку...",
        "freq_twice_daily": "двічі на день",
        "freq_four_daily": "4 рази на день (у пікові години)",
        "freq_every_15min": "Кожні 15 хв",
        "freq_every_nh": "кожні {n}г",
        "already_subscribed": "❌ Вже підписані на цю послугу.",
        "unsub_success": "✅ Підписку скасовано.",
        "unsub_fail": "❌ Не вдалося скасувати підписку.",
        "check_fail": "❌ Не вдалося виконати перевірку.",
        "found_apts_header": "✅ *Знайдено {n} запис(ів)!*\n\n",
        "apt_at": "о",
        "more_apts": "\n…і ще {n}",
        "no_apts": (
            "❌ Записи зараз недоступні.\n\n"
            "Бот повідомить вас, коли з'являться слоти."
        ),
        "check_error": "❌ Помилка: {msg}",
        "checking": "🔍 Перевіряю доступність… Зачекайте.",
        "premium_unavailable": "🚧 Premium-підписки тимчасово недоступні (незабаром).",
        "use_start": "❌ Спочатку використайте /start.",
        "already_premium": "✅ У вас вже є Premium!",
        "premium_no_user": "❌ Не вдалося активувати Premium — користувача не знайдено.",
        "premium_activated": (
            "🎉 *Premium активовано!*\n\nНеобмежені підписки.\n"
            "Використайте /setschedule <години> для налаштування графіку."
        ),
        "premium_only": "⚠️ Налаштований графік — функція Premium.\nВикористайте /premium.",
        "setschedule_usage": "Використання: /setschedule <години>\nПриклад: /setschedule 2",
        "hours_invalid": "❌ Години мають бути від 1 до 24.",
        "schedule_updated": "✅ Усі підписки тепер перевіряються кожні {n}г.",
        "language_choose": "🌐 *Оберіть мову:*",
        "language_set": "✅ Мову збережено.",
        "ad_premium_upsell": (
            "⭐ Безкоштовно: 4 перевірки/день. Преміум: кожні 15 хв — завжди першим, жоден слот не пропущений. /premium"
        ),
        "btn_get_premium": "⭐ Отримати Premium (незабаром)",
    },
    "tr": {
        "welcome": (
            "👋 Hoş geldiniz, {name}!\n\n"
            "Bu bot, Düsseldorf şehir hizmetleri için randevu müsaitliğini takip eder.\n\n"
            "Komutlar:\n"
            "/subscribe — Bir hizmete abone ol\n"
            "/list — Aboneliklerim\n"
            "/unsubscribe — Aboneliği iptal et\n"
            "/check — Manuel kontrol\n"
            "/language — Dil değiştir\n"
            "/help — Yardım\n\n"
            "Planınız: {plan}"
        ),
        "help_text": (
            "📖 *Yardım ve Komutlar*\n\n"
            "/start — Botu başlat\n"
            "/subscribe — Randevu bildirimlerine abone ol\n"
            "/list — Aktif abonelikler\n"
            "/unsubscribe — Aboneliği iptal et\n"
            "/check — Manuel kontrol\n"
            "/language — Dil değiştir\n"
            "/help — Bu mesaj\n\n"
            "*Nasıl çalışır:*\n"
            "1. /subscribe ile bir hizmete abone olun\n"
            "2. Bot otomatik kontrol eder ve slot açıldığında bildirir\n"
            "3. /list ve /unsubscribe ile abonelikleri yönetin\n\n"
            "*Planlar:*\n"
            "• ÜCRETSİZ: 3 aboneliğe kadar, 12 saatte bir kontrol\n"
            "• PREMIUM: Sınırsız abonelik, özel zamanlama"
        ),
        "user_not_found": "❌ Kullanıcı bulunamadı. Lütfen /start kullanın.",
        "no_subs": "📭 Aktif aboneliğiniz yok.\n\nBir hizmeti takip etmek için /subscribe kullanın.",
        "no_subs_short": "📭 Aktif abonelik yok.",
        "subs_header": "📋 *Aktif Abonelikleriniz:*\n\n",
        "interval_label": "Her {n}s",
        "last_check_label": "Son kontrol: {time}",
        "never": "Hiçbir zaman",
        "btn_unsub_prefix": "❌ İptal: ",
        "no_services": "❌ Şu anda hizmet yok.",
        "no_services_short": "❌ Hizmet yok.",
        "select_dept": "📝 *Departman seçin:*",
        "select_unsub": "🗑️ *İptal edilecek aboneliği seçin:*",
        "select_check": "🔍 *Kontrol edilecek aboneliği seçin:*",
        "cancelled": "❌ İptal edildi.",
        "btn_cancel": "❌ İptal",
        "btn_back": "⬅️ Geri",
        "dept_not_found": "❌ Departman bulunamadı.",
        "no_services_dept": "❌ Bu departmanda hizmet bulunamadı.",
        "select_cat": "Kategori seçin:",
        "cat_not_found": "❌ Kategori bulunamadı.",
        "no_services_cat": "❌ Hizmet bulunamadı.",
        "select_service": "Hizmet seçin:",
        "user_not_found_short": "❌ Kullanıcı bulunamadı.",
        "plan_limit": "❌ Ücretsiz plan: maksimum 3 abonelik.\n\nYükseltmek için /premium kullanın.",
        "subscribed": "✅ *Abone olundu!*\n\nHizmet: {name}\nKontroller: {freq}\n\nİlk kontrol başlatılıyor...",
        "freq_twice_daily": "günde iki kez",
        "freq_four_daily": "Günde 4× (yoğun saatlerde)",
        "freq_every_15min": "Her 15 dakika",
        "freq_every_nh": "her {n} saatte bir",
        "already_subscribed": "❌ Bu hizmete zaten abonesiniz.",
        "unsub_success": "✅ Abonelik iptal edildi.",
        "unsub_fail": "❌ Abonelik iptal edilemedi.",
        "check_fail": "❌ Kontrol başarısız.",
        "found_apts_header": "✅ *{n} randevu bulundu!*\n\n",
        "apt_at": "saat",
        "more_apts": "\n…ve {n} daha",
        "no_apts": (
            "❌ Şu anda randevu yok.\n\n"
            "Slot açıldığında bot sizi bildirecek."
        ),
        "check_error": "❌ Hata: {msg}",
        "checking": "🔍 Randevular kontrol ediliyor… Lütfen bekleyin.",
        "premium_unavailable": "🚧 Premium abonelikler şu anda kullanılamıyor (yakında).",
        "use_start": "❌ Önce /start kullanın.",
        "already_premium": "✅ Zaten Premium'sunuz!",
        "premium_no_user": "❌ Premium etkinleştirilemedi — kullanıcı bulunamadı.",
        "premium_activated": (
            "🎉 *Premium etkinleştirildi!*\n\nSınırsız abonelik.\n"
            "Kontrol sıklığını ayarlamak için /setschedule <saat> kullanın."
        ),
        "premium_only": "⚠️ Özel zamanlama Premium özelliğidir.\n/premium kullanın.",
        "setschedule_usage": "Kullanım: /setschedule <saat>\nÖrnek: /setschedule 2",
        "hours_invalid": "❌ Saat 1 ile 24 arasında olmalıdır.",
        "schedule_updated": "✅ Tüm abonelikler artık her {n} saatte bir kontrol edilecek.",
        "language_choose": "🌐 *Dil seçin:*",
        "language_set": "✅ Dil kaydedildi.",
        "ad_premium_upsell": (
            "⭐ Ücretsiz: günde 4 kontrol. Premium: her 15 dk — her zaman önce, hiçbir slotu kaçırma. /premium"
        ),
        "btn_get_premium": "⭐ Premium Al (yakında)",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    """Return translated string, falling back to English if lang or key missing."""
    text = STRINGS.get(lang, {}).get(key) or STRINGS["en"].get(key, key)
    return text.format(**kwargs) if kwargs else text
