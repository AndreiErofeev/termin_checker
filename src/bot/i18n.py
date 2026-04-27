"""Bot UI translations. All keys must exist in 'en'; other langs fall back to 'en'."""

STRINGS = {
    "en": {
        "welcome": (
            "👋 Welcome {name}!\n\n"
            "This bot monitors appointment availability for Düsseldorf city services.\n\n"
            "Commands:\n"
            "/subscribe — Subscribe to a service\n"
            "/list — View your subscriptions\n"
            "/unsubscribe — Remove a subscription\n"
            "/check — Manual check\n"
            "/language — Change language\n"
            "/premium — Upgrade to Premium\n"
            "/help — Help & all commands\n\n"
            "Your plan: {plan}"
        ),
        "help_text": (
            "📖 *Help & Commands*\n\n"
            "/subscribe — Subscribe to appointment notifications\n"
            "/list — View your active subscriptions\n"
            "/unsubscribe — Remove a subscription\n"
            "/check — Manually check for appointments\n"
            "/language — Change bot language\n"
            "/premium — Upgrade to Premium\n"
            "/help — This message\n\n"
            "*How it works:*\n"
            "1. Subscribe to a service via /subscribe\n"
            "2. Bot checks automatically and notifies you when slots open\n"
            "3. Manage subscriptions with /list and /unsubscribe\n\n"
            "*Plans:*\n"
            "• FREE: Up to 3 subscriptions, checks 4× daily\n"
            "• PREMIUM: Unlimited subscriptions, checks every 15 min, configurable reminders\n\n"
            "📋 /terms — Terms of Use"
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
        "cancelled": "OK.",
        "btn_cancel": "✖️ Close",
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
        "unsub_success": "✅ Unsubscribed.",
        "unsub_fail": "❌ Failed to unsubscribe.",
        "check_fail": "❌ Failed to run check.",
        "found_apts_header": "✅ *Found {n} appointment(s) for {name}!*\n\n",
        "apt_at": "at",
        "more_apts": "\n…and {n} more",
        "no_apts": (
            "❌ No appointments for *{name}* right now.\n\n"
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
            "Checks run every 15 min. Use /list to configure reminder frequency per subscription."
        ),
        "premium_only": "⚠️ Custom schedules are a Premium feature.\nUse /premium to upgrade.",
        "language_choose": "🌐 *Choose your language:*",
        "language_set": "✅ Language updated.",
        "ad_premium_upsell": (
            "⭐ Free: 4 checks/day. Premium: every 15 min — always first, never miss a slot. /premium"
        ),
        "btn_get_premium": "⭐ Get Premium (coming soon)",
        "terms_intro": "📋 *Terms of Use*",
        "confirm_sub_prompt": "Subscribe to *{name}*?",
        "confirm_unsub_prompt": "Unsubscribe from *{name}*?",
        "btn_yes_subscribe": "✅ Yes, subscribe",
        "btn_yes_unsubscribe": "🗑 Yes, unsubscribe",
        "notify_found_header": "🔔 *Appointments available for {name}!*\n\n",
        "notify_reminder_header": "⏰ *Still available — {name}:*\n\n",
        "notify_gone": "😔 No more appointments for *{name}* right now.\n\nI'll keep checking and notify you when they're back.",
        "notify_book_now": "\n🔗 Book now: {url}",
        "apt_date_summary": "📅 {date} — {n} slots from {first_time}",
        "more_dates": "…and {n} more date(s)",
        "btn_unsubscribe": "❌ Unsubscribe",
        "btn_change_reminder": "⚙️ Reminders",
        "reminder_picker_prompt": "⏰ *Reminder frequency*\nHow often should I remind you while appointments are available?\n\nCurrent: every {current}",
        "reminder_set": "✅ Got it — I'll remind you every {interval}.",
        "btn_keep_subscription": "⬅️ Keep subscription",
        "unsub_kept": "👍 Still monitoring.",
        "btn_no_subscribe": "✖️ No thanks",
        "sub_not_subscribed": "✖️ No subscription added.",
    },
    "de": {
        "welcome": (
            "👋 Willkommen, {name}!\n\n"
            "Dieser Bot überwacht Terminverfügbarkeiten bei Düsseldorfer Stadtdiensten.\n\n"
            "Befehle:\n"
            "/subscribe — Service abonnieren\n"
            "/list — Abonnements anzeigen\n"
            "/unsubscribe — Abonnement beenden\n"
            "/check — Manuelle Prüfung\n"
            "/language — Sprache ändern\n"
            "/premium — Auf Premium upgraden\n"
            "/help — Hilfe & alle Befehle\n\n"
            "Ihr Plan: {plan}"
        ),
        "help_text": (
            "📖 *Hilfe & Befehle*\n\n"
            "/subscribe — Terminbenachrichtigungen abonnieren\n"
            "/list — Aktive Abonnements anzeigen\n"
            "/unsubscribe — Abonnement beenden\n"
            "/check — Manuell nach Terminen suchen\n"
            "/language — Botsprache ändern\n"
            "/premium — Auf Premium upgraden\n"
            "/help — Diese Nachricht\n\n"
            "*So funktioniert es:*\n"
            "1. Abonnieren Sie einen Dienst über /subscribe\n"
            "2. Der Bot prüft automatisch und benachrichtigt Sie, wenn Termine frei werden\n"
            "3. Abonnements mit /list und /unsubscribe verwalten\n\n"
            "*Tarife:*\n"
            "• KOSTENLOS: Bis zu 3 Abonnements, 4× täglich\n"
            "• PREMIUM: Unbegrenzte Abonnements, alle 15 Min., konfigurierbare Erinnerungen\n\n"
            "📋 /terms — Nutzungsbedingungen"
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
        "cancelled": "OK.",
        "btn_cancel": "✖️ Schließen",
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
        "unsub_success": "✅ Abonnement beendet.",
        "unsub_fail": "❌ Kündigung fehlgeschlagen.",
        "check_fail": "❌ Prüfung fehlgeschlagen.",
        "found_apts_header": "✅ *{n} Termin(e) für {name} gefunden!*\n\n",
        "apt_at": "um",
        "more_apts": "\n…und {n} weitere",
        "no_apts": (
            "❌ Derzeit keine Termine für *{name}*.\n\n"
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
            "Prüfungen alle 15 Min. Erinnerungsintervall pro Abonnement in /list konfigurierbar."
        ),
        "premium_only": "⚠️ Individuelle Zeitpläne sind ein Premium-Feature.\nMit /premium upgraden.",
        "language_choose": "🌐 *Sprache wählen:*",
        "language_set": "✅ Sprache gespeichert.",
        "ad_premium_upsell": (
            "⭐ Free: 4 Checks/Tag. Premium: alle 15 Min. — immer zuerst, kein Slot verpasst. /premium"
        ),
        "btn_get_premium": "⭐ Premium holen (demnächst)",
        "terms_intro": "📋 *Nutzungsbedingungen*",
        "confirm_sub_prompt": "Abonnieren *{name}*?",
        "confirm_unsub_prompt": "Abonnement von *{name}* kündigen?",
        "btn_yes_subscribe": "✅ Ja, abonnieren",
        "btn_yes_unsubscribe": "🗑 Ja, kündigen",
        "notify_found_header": "🔔 *Termine verfügbar für {name}!*\n\n",
        "notify_reminder_header": "⏰ *Noch verfügbar — {name}:*\n\n",
        "notify_gone": "😔 Keine Termine mehr für *{name}* verfügbar.\n\nIch prüfe weiter und benachrichtige Sie, sobald wieder Slots frei sind.",
        "notify_book_now": "\n🔗 Jetzt buchen: {url}",
        "apt_date_summary": "📅 {date} — {n} Termine ab {first_time}",
        "more_dates": "…und {n} weitere Datum/Daten",
        "btn_unsubscribe": "❌ Abonnement kündigen",
        "btn_change_reminder": "⚙️ Erinnerungen",
        "reminder_picker_prompt": "⏰ *Erinnerungsintervall*\nWie oft soll ich Sie erinnern, solange Termine verfügbar sind?\n\nAktuell: alle {current}",
        "reminder_set": "✅ Gespeichert — ich erinnere alle {interval}.",
        "btn_keep_subscription": "⬅️ Abonnement behalten",
        "unsub_kept": "👍 Weiter wird überwacht.",
        "btn_no_subscribe": "✖️ Nein danke",
        "sub_not_subscribed": "✖️ Nicht abonniert.",
    },
    "ru": {
        "welcome": (
            "👋 Добро пожаловать, {name}!\n\n"
            "Этот бот отслеживает доступность записи в службы города Дюссельдорф.\n\n"
            "Команды:\n"
            "/subscribe — Подписаться на услугу\n"
            "/list — Мои подписки\n"
            "/unsubscribe — Отписаться от услуги\n"
            "/check — Проверить вручную\n"
            "/language — Изменить язык\n"
            "/premium — Перейти на Premium\n"
            "/help — Помощь и все команды\n\n"
            "Ваш тариф: {plan}"
        ),
        "help_text": (
            "📖 *Помощь и команды*\n\n"
            "/subscribe — Подписаться на уведомления о записи\n"
            "/list — Активные подписки\n"
            "/unsubscribe — Отписаться от услуги\n"
            "/check — Ручная проверка\n"
            "/language — Изменить язык\n"
            "/premium — Перейти на Premium\n"
            "/help — Это сообщение\n\n"
            "*Как это работает:*\n"
            "1. Подпишитесь на услугу через /subscribe\n"
            "2. Бот автоматически проверяет и уведомляет, когда появляются слоты\n"
            "3. Управляйте подписками через /list и /unsubscribe\n\n"
            "*Тарифы:*\n"
            "• БЕСПЛАТНО: до 3 подписок, 4 проверки в день\n"
            "• PREMIUM: безлимитные подписки, каждые 15 мин., настраиваемые напоминания\n\n"
            "📋 /terms — Условия использования"
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
        "cancelled": "OK.",
        "btn_cancel": "✖️ Закрыть",
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
        "unsub_success": "✅ Подписка отключена.",
        "unsub_fail": "❌ Не удалось отписаться.",
        "check_fail": "❌ Не удалось выполнить проверку.",
        "found_apts_header": "✅ *Найдено {n} запис(ей) для {name}!*\n\n",
        "apt_at": "в",
        "more_apts": "\n…и ещё {n}",
        "no_apts": (
            "❌ Записи для *{name}* сейчас недоступны.\n\n"
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
            "Проверки каждые 15 мин. Частота напоминаний настраивается в /list."
        ),
        "premium_only": "⚠️ Настраиваемое расписание — функция Premium.\nИспользуйте /premium.",
        "language_choose": "🌐 *Выберите язык:*",
        "language_set": "✅ Язык сохранён.",
        "ad_premium_upsell": (
            "⭐ Бесплатно: 4 проверки/день. Премиум: каждые 15 мин — всегда первым, ни один слот не пропущен. /premium"
        ),
        "btn_get_premium": "⭐ Получить Premium (скоро)",
        "confirm_sub_prompt": "Подписаться на *{name}*?",
        "confirm_unsub_prompt": "Отписаться от *{name}*?",
        "btn_yes_subscribe": "✅ Да, подписаться",
        "btn_yes_unsubscribe": "🗑 Да, отписаться",
        "notify_found_header": "🔔 *Записи доступны для {name}!*\n\n",
        "notify_reminder_header": "⏰ *Ещё доступно — {name}:*\n\n",
        "notify_gone": "😔 Записи для *{name}* больше недоступны.\n\nБот продолжит проверку и уведомит вас, когда появятся слоты.",
        "notify_book_now": "\n🔗 Записаться: {url}",
        "apt_date_summary": "📅 {date} — {n} записей с {first_time}",
        "more_dates": "…и ещё {n} дат",
        "btn_unsubscribe": "❌ Отписаться",
        "btn_change_reminder": "⚙️ Напоминания",
        "reminder_picker_prompt": "⏰ *Частота напоминаний*\nКак часто напоминать о доступных записях?\n\nТекущее: каждые {current}",
        "reminder_set": "✅ Сохранено — буду напоминать каждые {interval}.",
        "btn_keep_subscription": "⬅️ Оставить подписку",
        "unsub_kept": "👍 Мониторинг продолжается.",
        "btn_no_subscribe": "✖️ Нет, спасибо",
        "sub_not_subscribed": "✖️ Подписка не оформлена.",
    },
    "uk": {
        "welcome": (
            "👋 Вітаємо, {name}!\n\n"
            "Цей бот відстежує доступність запису до служб міста Дюссельдорф.\n\n"
            "Команди:\n"
            "/subscribe — Підписатися на послугу\n"
            "/list — Мої підписки\n"
            "/unsubscribe — Відписатися від послуги\n"
            "/check — Перевірити вручну\n"
            "/language — Змінити мову\n"
            "/premium — Перейти на Premium\n"
            "/help — Допомога та всі команди\n\n"
            "Ваш тариф: {plan}"
        ),
        "help_text": (
            "📖 *Допомога та команди*\n\n"
            "/subscribe — Підписатися на сповіщення про запис\n"
            "/list — Активні підписки\n"
            "/unsubscribe — Відписатися від послуги\n"
            "/check — Ручна перевірка\n"
            "/language — Змінити мову\n"
            "/premium — Перейти на Premium\n"
            "/help — Це повідомлення\n\n"
            "*Як це працює:*\n"
            "1. Підпишіться на послугу через /subscribe\n"
            "2. Бот автоматично перевіряє та сповіщає, коли з'являються слоти\n"
            "3. Керуйте підписками через /list та /unsubscribe\n\n"
            "*Тарифи:*\n"
            "• БЕЗКОШТОВНО: до 3 підписок, 4 перевірки на день\n"
            "• PREMIUM: необмежені підписки, кожні 15 хв., налаштовані нагадування\n\n"
            "📋 /terms — Умови використання"
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
        "cancelled": "OK.",
        "btn_cancel": "✖️ Закрити",
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
        "unsub_success": "✅ Підписку відключено.",
        "unsub_fail": "❌ Не вдалося відписатися.",
        "check_fail": "❌ Не вдалося виконати перевірку.",
        "found_apts_header": "✅ *Знайдено {n} запис(ів) для {name}!*\n\n",
        "apt_at": "о",
        "more_apts": "\n…і ще {n}",
        "no_apts": (
            "❌ Записи для *{name}* зараз недоступні.\n\n"
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
            "Перевірки кожні 15 хв. Частота нагадувань налаштовується в /list."
        ),
        "premium_only": "⚠️ Налаштований графік — функція Premium.\nВикористайте /premium.",
        "language_choose": "🌐 *Оберіть мову:*",
        "language_set": "✅ Мову збережено.",
        "ad_premium_upsell": (
            "⭐ Безкоштовно: 4 перевірки/день. Преміум: кожні 15 хв — завжди першим, жоден слот не пропущений. /premium"
        ),
        "btn_get_premium": "⭐ Отримати Premium (незабаром)",
        "confirm_sub_prompt": "Підписатися на *{name}*?",
        "confirm_unsub_prompt": "Відписатися від *{name}*?",
        "btn_yes_subscribe": "✅ Так, підписатися",
        "btn_yes_unsubscribe": "🗑 Так, відписатися",
        "notify_found_header": "🔔 *Записи доступні для {name}!*\n\n",
        "notify_reminder_header": "⏰ *Ще доступно — {name}:*\n\n",
        "notify_gone": "😔 Записи для *{name}* більше недоступні.\n\nБот продовжить перевірку та повідомить, коли з'являться слоти.",
        "notify_book_now": "\n🔗 Записатися: {url}",
        "apt_date_summary": "📅 {date} — {n} записів з {first_time}",
        "more_dates": "…і ще {n} дат",
        "btn_unsubscribe": "❌ Відписатися",
        "btn_change_reminder": "⚙️ Нагадування",
        "reminder_picker_prompt": "⏰ *Частота нагадувань*\nЯк часто нагадувати про доступні записи?\n\nПоточне: кожні {current}",
        "reminder_set": "✅ Збережено — нагадуватиму кожні {interval}.",
        "btn_keep_subscription": "⬅️ Залишити підписку",
        "unsub_kept": "👍 Моніторинг триває.",
        "btn_no_subscribe": "✖️ Ні, дякую",
        "sub_not_subscribed": "✖️ Не підписано.",
    },
    "tr": {
        "welcome": (
            "👋 Hoş geldiniz, {name}!\n\n"
            "Bu bot, Düsseldorf şehir hizmetleri için randevu müsaitliğini takip eder.\n\n"
            "Komutlar:\n"
            "/subscribe — Bir hizmete abone ol\n"
            "/list — Aboneliklerim\n"
            "/unsubscribe — Aboneliği sonlandır\n"
            "/check — Manuel kontrol\n"
            "/language — Dil değiştir\n"
            "/premium — Premium'a yükselt\n"
            "/help — Yardım ve tüm komutlar\n\n"
            "Planınız: {plan}"
        ),
        "help_text": (
            "📖 *Yardım ve Komutlar*\n\n"
            "/subscribe — Randevu bildirimlerine abone ol\n"
            "/list — Aktif abonelikler\n"
            "/unsubscribe — Aboneliği sonlandır\n"
            "/check — Manuel kontrol\n"
            "/language — Dil değiştir\n"
            "/premium — Premium'a yükselt\n"
            "/help — Bu mesaj\n\n"
            "*Nasıl çalışır:*\n"
            "1. /subscribe ile bir hizmete abone olun\n"
            "2. Bot otomatik kontrol eder ve slot açıldığında bildirir\n"
            "3. /list ve /unsubscribe ile abonelikleri yönetin\n\n"
            "*Planlar:*\n"
            "• ÜCRETSİZ: 3 aboneliğe kadar, günde 4 kontrol\n"
            "• PREMIUM: Sınırsız abonelik, 15 dk'da bir, yapılandırılabilir hatırlatmalar\n\n"
            "📋 /terms — Kullanım Koşulları"
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
        "cancelled": "OK.",
        "btn_cancel": "✖️ Kapat",
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
        "unsub_success": "✅ Abonelikten çıkıldı.",
        "unsub_fail": "❌ Abonelik sonlandırılamadı.",
        "check_fail": "❌ Kontrol başarısız.",
        "found_apts_header": "✅ *{name} için {n} randevu bulundu!*\n\n",
        "apt_at": "saat",
        "more_apts": "\n…ve {n} daha",
        "no_apts": (
            "❌ *{name}* için şu anda randevu yok.\n\n"
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
            "Kontroller 15 dk'da bir çalışır. Hatırlatma sıklığını /list üzerinden ayarlayın."
        ),
        "premium_only": "⚠️ Özel zamanlama Premium özelliğidir.\n/premium kullanın.",
        "language_choose": "🌐 *Dil seçin:*",
        "language_set": "✅ Dil kaydedildi.",
        "ad_premium_upsell": (
            "⭐ Ücretsiz: günde 4 kontrol. Premium: her 15 dk — her zaman önce, hiçbir slotu kaçırma. /premium"
        ),
        "btn_get_premium": "⭐ Premium Al (yakında)",
        "confirm_sub_prompt": "*{name}* hizmetine abone ol?",
        "confirm_unsub_prompt": "*{name}* aboneliğini iptal et?",
        "btn_yes_subscribe": "✅ Evet, abone ol",
        "btn_yes_unsubscribe": "🗑 Evet, aboneliği bitir",
        "notify_found_header": "🔔 *{name} için randevu mevcut!*\n\n",
        "notify_reminder_header": "⏰ *Hâlâ mevcut — {name}:*\n\n",
        "notify_gone": "😔 *{name}* için artık randevu yok.\n\nKontrol etmeye devam edeceğim, slot açıldığında bildireceğim.",
        "notify_book_now": "\n🔗 Şimdi rezervasyon yap: {url}",
        "apt_date_summary": "📅 {date} — {n} slot ({first_time}'dan itibaren)",
        "more_dates": "…ve {n} tarih daha",
        "btn_unsubscribe": "❌ Aboneliği iptal et",
        "btn_change_reminder": "⚙️ Hatırlatmalar",
        "reminder_picker_prompt": "⏰ *Hatırlatma sıklığı*\nRandevular açıkken ne sıklıkta hatırlatayım?\n\nŞu an: her {current}",
        "reminder_set": "✅ Tamam — her {interval} hatırlatacağım.",
        "btn_keep_subscription": "⬅️ Aboneliği koru",
        "unsub_kept": "👍 Takip devam ediyor.",
        "btn_no_subscribe": "✖️ Hayır, teşekkürler",
        "sub_not_subscribed": "✖️ Abone olunmadı.",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    """Return translated string, falling back to English if lang or key missing."""
    text = STRINGS.get(lang, {}).get(key) or STRINGS["en"].get(key, key)
    return text.format(**kwargs) if kwargs else text


def format_apt_grouped(appointments, lang: str) -> str:
    """Group appointments by date; show up to 3 dates with slot count and first time."""
    from collections import defaultdict
    by_date: dict[str, list[str]] = defaultdict(list)
    for apt in appointments:
        by_date[apt.appointment_date].append(apt.appointment_time)

    lines = []
    for date in sorted(by_date.keys())[:7]:
        times = sorted(by_date[date])
        n = len(times)
        if n == 1:
            lines.append(f"📅 {date} {t(lang, 'apt_at')} {times[0]}")
        else:
            lines.append(t(lang, "apt_date_summary", date=date, n=n, first_time=times[0]))

    remaining = len(by_date) - min(len(by_date), 7)
    if remaining > 0:
        lines.append(t(lang, "more_dates", n=remaining))

    return "\n".join(lines)
