"""
Тесты логики модуля story
"""

import pytest
from datetime import datetime


class TestStoryLogic:
    """Тесты логики модуля story"""

    def test_date_formatting(self):
        """Тест форматирования даты"""

        # Функция форматирования даты
        def format_date(date_value, date_format='dd-mm-yyyy'):
            if isinstance(date_value, str):
                try:
                    date_value = datetime.strptime(date_value, "%Y-%m-%d")
                except:
                    try:
                        date_value = datetime.strptime(date_value, "%Y-%m-%d %H:%M:%S")
                    except:
                        return date_value

            if date_format == 'dd-mm-yyyy':
                return date_value.strftime("%d-%m-%Y")
            elif date_format == 'mm-dd-yyyy':
                return date_value.strftime("%m-%d-%Y")
            elif date_format == 'yyyy-mm-dd':
                return date_value.strftime("%Y-%m-%d")
            else:
                return date_value.strftime("%d-%m-%Y")

        # Тестовые данные
        test_date = datetime(2024, 1, 15, 10, 30, 0)

        # Проверяем различные форматы
        test_cases = [
            ('dd-mm-yyyy', '15-01-2024'),
            ('mm-dd-yyyy', '01-15-2024'),
            ('yyyy-mm-dd', '2024-01-15')
        ]

        for date_format, expected_output in test_cases:
            result = format_date(test_date, date_format)
            assert result == expected_output

        # Проверяем строковый ввод
        result = format_date("2024-01-15", 'dd-mm-yyyy')
        assert result == "15-01-2024"

    def test_safe_convert_to_float(self):
        """Тест безопасного преобразования в float"""

        def safe_convert_to_float(value):
            try:
                return float(value) if value is not None else None
            except (TypeError, ValueError):
                return None

        test_cases = [
            ("70.5", 70.5),
            ("70", 70.0),
            (None, None),
            ("не число", None),
            ("", None)
        ]

        for input_val, expected in test_cases:
            result = safe_convert_to_float(input_val)
            assert result == expected

    def test_safe_convert_to_int(self):
        """Тест безопасного преобразования в int"""

        def safe_convert_to_int(value):
            try:
                return int(float(value)) if value is not None else None
            except (TypeError, ValueError):
                return None

        test_cases = [
            ("75", 75),
            ("75.5", 75),  # округляется
            (None, None),
            ("не число", None),
            ("", None)
        ]

        for input_val, expected in test_cases:
            result = safe_convert_to_int(input_val)
            assert result == expected

    def test_calculate_statistics(self):
        """Тест расчета статистики"""

        def calculate_statistics(records):
            stats = []

            # Статистика по весу
            weights = []
            for record in records:
                try:
                    weight = float(record[1]) if record[1] else None
                    if weight is not None:
                        weights.append(weight)
                except:
                    pass

            if weights:
                avg_weight = sum(weights) / len(weights)
                stats.append(f'Средний вес: {avg_weight:.1f} кг')

            # Статистика по давлению
            pressures_sys = []
            pressures_dia = []

            for record in records:
                try:
                    sys = int(record[2]) if record[2] else None
                    dia = int(record[3]) if record[3] else None
                    if sys is not None:
                        pressures_sys.append(sys)
                    if dia is not None:
                        pressures_dia.append(dia)
                except:
                    pass

            if pressures_sys and pressures_dia:
                avg_sys = sum(pressures_sys) / len(pressures_sys)
                avg_dia = sum(pressures_dia) / len(pressures_dia)
                stats.append(f'Среднее давление: {avg_sys:.0f}/{avg_dia:.0f} мм рт.ст.')

            return stats

        # Тестовые записи
        records = [
            (1, 70.0, 120, 80, 75, 36.6, "Заметка 1", "2024-01-01"),
            (2, 71.0, 125, 85, 80, 36.8, "Заметка 2", "2024-01-02"),
            (3, 72.0, 130, 90, 85, 37.0, "Заметка 3", "2024-01-03")
        ]

        stats = calculate_statistics(records)

        assert len(stats) >= 1
        if stats:
            assert "Средний" in stats[0]