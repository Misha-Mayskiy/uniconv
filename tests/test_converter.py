import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from library import UnitConverter, UnknownUnitError, UnknownParameterError


class TestUnitConverter(unittest.TestCase):

    def setUp(self):
        """Создает экземпляр конвертера перед каждым тестом."""
        self.uc = UnitConverter()
        self.precision = 7

    def test_pressure_conversions(self):
        """Тестирование конверсий давления."""
        # кгс/см² в МПа (1 кгс/см² = 0.0980665 МПа)
        self.assertAlmostEqual(self.uc.convert(1, from_unit="кгс/см²", to_unit="МПа", parameter_type="pressure"),
                               0.0980665, self.precision)
        # бар в Па (1 бар = 100 000 Па)
        self.assertAlmostEqual(self.uc.convert(1, from_unit="бар", to_unit="Па", parameter_type="pressure"), 100000,
                               self.precision)
        # МПа в кгс/см²
        self.assertAlmostEqual(self.uc.convert(1, from_unit="МПа", to_unit="кгс/см²", parameter_type="pressure"),
                               10.1971621, self.precision)

    def test_temperature_conversions(self):
        """Тестирование нелинейной конверсии температуры."""
        # °C в K
        self.assertAlmostEqual(self.uc.convert(100, from_unit="°C", to_unit="K", parameter_type="temperature"), 373.15,
                               self.precision)
        # K в °C
        self.assertAlmostEqual(self.uc.convert(0, from_unit="K", to_unit="°C", parameter_type="temperature"), -273.15,
                               self.precision)
        # Отрицательная температура
        self.assertAlmostEqual(self.uc.convert(-40, from_unit="°C", to_unit="K", parameter_type="temperature"), 233.15,
                               self.precision)

    def test_power_conversions(self):
        """Тестирование конверсий мощности."""
        # МВт в кВт
        self.assertEqual(self.uc.convert(1, from_unit="МВт", to_unit="кВт", parameter_type="power"), 1000)
        # кВт в л.с. (1 кВт ≈ 1.35962 л.с.)
        self.assertAlmostEqual(self.uc.convert(100, from_unit="кВт", to_unit="л.с.", parameter_type="power"), 135.9621617,
                               self.precision)
        # л.с. в МВт
        self.assertAlmostEqual(self.uc.convert(1, from_unit="л.с.", to_unit="МВт", parameter_type="power"),
                               0.00073549875, self.precision)

    def test_enthalpy_conversions(self):
        """Тестирование конверсий энтальпии."""
        # ккал/кг в кДж/кг (1 ккал = 4.1868 кДж)
        self.assertAlmostEqual(
            self.uc.convert(100, from_unit="ккал/кг", to_unit="кДж/кг", parameter_type="specific_enthalpy"), 418.68,
            self.precision)
        # кДж/кг в ккал/кг
        self.assertAlmostEqual(
            self.uc.convert(1000, from_unit="кДж/кг", to_unit="ккал/кг", parameter_type="specific_enthalpy"), 238.8458966,
            self.precision)

    def test_dryness_fraction_conversion(self):
        """Тестирование конверсии степени сухости."""
        # Проценты в долю
        self.assertAlmostEqual(self.uc.convert(95, from_unit="%", to_unit="доля", parameter_type="dryness_fraction"),
                               0.95, self.precision)
        # Доля в проценты
        self.assertAlmostEqual(self.uc.convert(0.88, from_unit="доля", to_unit="%", parameter_type="dryness_fraction"),
                               88, self.precision)

    def test_identity_conversion(self):
        """Тестирование конверсии единицы в саму себя."""
        self.assertAlmostEqual(self.uc.convert(123, from_unit="МПа", to_unit="МПа", parameter_type="pressure"), 123)
        self.assertEqual(self.uc.convert(45, from_unit="°C", to_unit="°C", parameter_type="temperature"), 45)

    def test_error_handling(self):
        """Тестирование вызова исключений при неверных входных данных."""
        # Неизвестная единица измерения
        with self.assertRaises(UnknownUnitError):
            self.uc.convert(10, from_unit="МПа", to_unit="неизвестная_единица", parameter_type="pressure")

        # Неизвестный тип параметра
        with self.assertRaises(UnknownParameterError):
            self.uc.convert(10, from_unit="кг", to_unit="г", parameter_type="масса")

        # Конверсия между разными параметрами (не должна быть возможна)
        with self.assertRaises(UnknownUnitError):
            self.uc.convert(10, from_unit="МПа", to_unit="°C", parameter_type="pressure")

    def test_dynamic_addition(self):
        """Тестирование динамического добавления параметров и единиц."""
        # Добавление нового параметра
        self.uc.add_parameter(
            parameter_type="speed",
            parameter_name="Скорость",
            base_unit_symbol="м/с",
            base_unit_name="Метр в секунду"
        )
        self.assertIn("speed", self.uc.parameters)
        self.assertEqual(self.uc.get_base_unit("speed"), "м/с")

        # Добавление новой единицы
        self.uc.add_unit(
            parameter_type="speed",
            unit_symbol="км/ч",
            unit_name="Километр в час",
            to_base=1 / 3.6,  # 1 км/ч = 1/3.6 м/с
            from_base=3.6
        )
        self.assertIn("км/ч", self.uc.get_available_units("speed"))

        # Проверка конверсии для нового параметра
        self.assertAlmostEqual(self.uc.convert(36, from_unit="км/ч", to_unit="м/с", parameter_type="speed"), 10,
                               self.precision)
        self.assertAlmostEqual(self.uc.convert(20, from_unit="м/с", to_unit="км/ч", parameter_type="speed"), 72,
                               self.precision)


if __name__ == '__main__':
    unittest.main()
