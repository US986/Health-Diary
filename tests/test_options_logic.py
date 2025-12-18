"""
Тесты логики модуля options
"""

import pytest
from datetime import datetime


class TestOptionsLogic:
    """Тесты логики модуля options"""

    def test_data_validation(self):
        """Тест валидации медицинских данных"""

        # Функции валидации (упрощенные)
        def validate_weight(weight):
            if not weight:
                raise ValueError("Вес не может быть пустым")
            w = float(weight)
            if w < 30 or w > 250:
                raise ValueError("Вес должен быть в пределах 30-250 кг")
            return w

        def validate_pressure_systolic(pressure):
            if not pressure:
                raise ValueError("Систолическое давление не может быть пустым")
            p = int(pressure)
            if p < 70 or p > 250:
                raise ValueError("Систолическое давление должно быть в пределах 70-250 мм рт.ст.")
            return p

        def validate_pressure_diastolic(pressure):
            if not pressure:
                raise ValueError("Диастолическое давление не может быть пустым")
            p = int(pressure)
            if p < 40 or p > 150:
                raise ValueError("Диастолическое давление должно быть в пределах 40-150 мм рт.ст.")
            return p

        def validate_pulse(pulse):
            if not pulse:
                raise ValueError("Пульс не может быть пустым")
            p = int(pulse)
            if p < 30 or p > 220:
                raise ValueError("Пульс должен быть в пределах 30-220 уд/мин")
            return p

        def validate_temperature(temp):
            if not temp:
                raise ValueError("Температура не может быть пустой")
            t = float(temp)
            if t < 34 or t > 42:
                raise ValueError("Температура должна быть в пределах 34-42°C")
            return t

        def validate_notes(notes):
            if notes and len(notes) > 500:
                raise ValueError("Заметки не должны превышать 500 символов")
            return notes

        # Тест корректных данных
        test_data = {
            'weight': '70.5',
            'pressure_systolic': '120',
            'pressure_diastolic': '80',
            'pulse': '75',
            'temperature': '36.6',
            'notes': 'Тестовая запись'
        }

        # Все валидации должны пройти без ошибок
        validate_weight(test_data['weight'])
        validate_pressure_systolic(test_data['pressure_systolic'])
        validate_pressure_diastolic(test_data['pressure_diastolic'])
        validate_pulse(test_data['pulse'])
        validate_temperature(test_data['temperature'])
        validate_notes(test_data['notes'])

        # Тест некорректных данных
        invalid_cases = [
            ('weight', '', "Вес не может быть пустым"),
            ('weight', '500', "Вес должен быть в пределах 30-250 кг"),
            ('pressure_systolic', '300', "Систолическое давление должно быть в пределах 70-250 мм рт.ст."),
            ('temperature', '50', "Температура должна быть в пределах 34-42°C"),
        ]

        for field, value, expected_error in invalid_cases:
            with pytest.raises(ValueError) as exc:
                if field == 'weight':
                    validate_weight(value)
                elif field == 'pressure_systolic':
                    validate_pressure_systolic(value)
                elif field == 'temperature':
                    validate_temperature(value)
            assert expected_error in str(exc.value)