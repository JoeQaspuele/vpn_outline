#Хэндлер кнопки проверки трафика
@bot.message_handler(func=lambda message: message.text == Buttons.CHECK_TRAFFIC)
def handle_check_traffic(message):
    user_id = message.chat.id
    key_id = db.get_user_key(user_id)

    if not key_id:
        bot.send_message(user_id, PremiumMessages.NO_KEY_FOUND)
        return

    try:
        # Получаем все данные из БД
        user_data = db.get_user_data(user_id)
        print("[DEBUG] user_data:", user_data)

        key = outline.get_key_by_id(key_id, DEFAULT_SERVER_ID)

        # Использовано всего
        total_used_bytes = key.used or 0
        total_used_gb = round(total_used_bytes / 1024**3, 2)

        # Получаем точку отсчёта для месяца
        start_bytes, start_date_str = db.get_traffic_reset_info(user_id)
        start_bytes = start_bytes or 0
        now = datetime.now()

        # Обновляем точку отсчета, если первый запуск или месяц сменился
        if not start_date_str:
            db.set_traffic_reset_info(user_id, total_used_bytes)
            used_this_month_gb = 0
        else:
            start_date = datetime.fromisoformat(start_date_str)
            if start_date.month != now.month or start_date.year != now.year:
                db.set_traffic_reset_info(user_id, total_used_bytes)
                used_this_month_gb = 0
            else:
                delta = max(0, total_used_bytes - start_bytes)
                used_this_month_gb = round(delta / 1024**3, 2)

        # Считаем остаток
        current_limit_gb = user_data.get("limit", 15)
        remaining_gb = max(0, current_limit_gb - used_this_month_gb)

        # PREMIUM
        # PREMIUM
        since_str = user_data.get("premium_since")
        until_str = user_data.get("premium_until")

        if user_data.get("isPremium") and since_str:
            since = datetime.fromisoformat(since_str)
            until = datetime.fromisoformat(until_str) if until_str else since + timedelta(days=31)
            bot.send_message(
                user_id,
                PremiumMessages.TRAFFIC_INFO_WITH_PREMIUM.format(
                    remaining=remaining_gb,
                    used=used_this_month_gb,
                    limit=current_limit_gb,
                    total=total_used_gb,
                    since=since.strftime('%d.%m.%Y'),
                    until=until.strftime('%d.%m.%Y')
                ),
                parse_mode="HTML"
            )
        else:
            bot.send_message(
                user_id,
                PremiumMessages.TRAFFIC_INFO.format(
                    remaining=remaining_gb,
                    used=used_this_month_gb,
                    limit=current_limit_gb,
                    total=total_used_gb
                ),
                parse_mode="HTML"
            )

    except Exception as e:
        bot.send_message(user_id, f"⚠️ Ошибка при получении трафика: {e}")
        print(f"[ERROR] handle_check_traffic: {e}")
