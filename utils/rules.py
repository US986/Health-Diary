import re

# --------------------
# ВАЛИДАЦИЯ ДЛЯ РЕГИСТРАЦИИ / ВХОДА
# --------------------

def validate_email(value: str) -> str:
    if not value or not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', value):
        raise ValueError("Введите корректный email (например: user@example.com).")
    return value.strip()


def validate_name(value: str) -> str:
    if not value.strip():
        raise ValueError("Имя не может быть пустым.")
    if len(value.strip()) > 100:
        raise ValueError("Имя слишком длинное (максимум 100 символов).")
    if not value.replace(" ", "").isalpha():
        raise ValueError("Имя может содержать только буквы и пробелы.")
    return value.strip()


def validate_password(password: str, confirm: str = None) -> str:
    if not password:
        raise ValueError("Пароль не может быть пустым.")
    if len(password) < 6:
        raise ValueError("Пароль должен содержать минимум 6 символов.")
    if confirm is not None and password != confirm:
        raise ValueError("Пароли не совпадают.")
    if not re.search(r"\d", password):
        raise ValueError("Пароль должен содержать хотя бы одну цифру.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Пароль должен содержать хотя бы одну заглавную букву.")
    return password


# --------------------
# ОЦЕНКА СЛОЖНОСТИ ПАРОЛЯ
# --------------------
def evaluate_password_strength(password: str) -> str:
    length_score = len(password) >= 8

    digit_score = bool(re.search(r"\d", password))

    uppercase_score = bool(re.search(r"[A-Z]", password))

    lowercase_score = bool(re.search(r"[a-z]", password))

    special_char_score = bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", password))

    score = sum([length_score, digit_score, uppercase_score, lowercase_score, special_char_score])

    if score <= 2:
        return "Слабый", (1, 0, 0, 1)
    elif score == 3:
        return "Средний", (1, 1, 0, 1)
    else:
        return "Сильный", (0, 1, 0, 1)


# --------------------
# ВАЛИДАЦИЯ ДАННЫХ ЗДОРОВЬЯ (ОПЦИИ / ИСТОРИЯ)
# --------------------

def validate_weight(weight: str) -> float:
    try:
        value = float(weight.replace(",", "."))
        if 20 <= value <= 500:
            return value
        raise ValueError("Вес должен быть в диапазоне 20–500 кг. Например: 70")
    except ValueError:
        raise ValueError("Введите корректный вес (число). Допустимо: 20–500 кг.")


def validate_pressure_systolic(value: str) -> int:
    try:
        val = int(value)
        if 70 <= val <= 250:
            return val
        raise ValueError("Систолическое давление должно быть в диапазоне 70–250 мм рт. ст. Например: 120")
    except ValueError:
        raise ValueError("Введите корректное систолическое давление (целое число). Допустимо: 70–250.")


def validate_pressure_diastolic(value: str) -> int:
    try:
        val = int(value)
        if 40 <= val <= 150:
            return val
        raise ValueError("Диастолическое давление должно быть в диапазоне 40–150 мм рт. ст. Например: 80")
    except ValueError:
        raise ValueError("Введите корректное диастолическое давление (целое число). Допустимо: 40–150.")


def validate_pulse(value: str) -> int:
    try:
        val = int(value)
        if 30 <= val <= 220:
            return val
        raise ValueError("Пульс должен быть в диапазоне 30–220 уд/мин. Например: 75")
    except ValueError:
        raise ValueError("Введите корректный пульс (целое число). Допустимо: 30–220.")


def validate_temperature(value: str) -> float:
    try:
        val = float(value.replace(",", "."))
        if 30 <= val <= 45:
            return val
        raise ValueError("Температура должна быть в диапазоне 30–45 °C. Например: 36.6")
    except ValueError:
        raise ValueError("Введите корректную температуру (например: 36.6). Допустимо: 30–45 °C.")


def validate_notes(value: str) -> str:
    text = value.strip()
    if len(text) > 500:
        raise ValueError("Заметка слишком длинная (максимум 500 символов).")
    if re.search(r"<.*?>", text):
        raise ValueError("Заметка не может содержать HTML теги.")
    return text
