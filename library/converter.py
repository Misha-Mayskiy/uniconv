from __future__ import annotations
from typing import Callable, Union, Dict, Any
from . import constants as const

Number = Union[int, float]
FactorOrFunc = Union[Number, Callable[[Number], Number]]


class UnknownParameterError(ValueError):
    """Исключение для неизвестного типа параметра."""
    pass


class UnknownUnitError(ValueError):
    """Исключение для неизвестной единицы измерения."""
    pass


class UnitConverter:
    """
    Универсальный и расширяемый конвертер инженерных единиц измерения,
    ориентированный на термодинамические расчеты.
    """

    def __init__(self) -> None:
        self.parameters: Dict[str, Dict[str, Any]] = {}
        self._build_defaults()

    # ------------------------ PUBLIC API -----------------------------
    def convert(self, value: Number, *,
                from_unit: str,
                to_unit: str,
                parameter_type: str) -> float:
        """
        Универсальная конвертация между двумя единицами одного параметра.
        """
        p_type = self._norm_param(parameter_type)
        base_val = self.to_base(value, from_unit=from_unit, parameter_type=p_type)
        return self.from_base(base_val, to_unit=to_unit, parameter_type=p_type)

    def to_base(self, value: Number, *, from_unit: str, parameter_type: str) -> float:
        """Перевод `value` из `from_unit` в базовую единицу параметра."""
        p_type = self._norm_param(parameter_type)
        unit = self._get_unit(p_type, from_unit)
        return unit["to_base"](value)

    def from_base(self, value: Number, *, to_unit: str, parameter_type: str) -> float:
        """Перевод `value` из базовой единицы в `to_unit`."""
        p_type = self._norm_param(parameter_type)
        unit = self._get_unit(p_type, to_unit)
        return unit["from_base"](value)

    def get_available_units(self, parameter_type: str) -> list[str]:
        """Возвращает список всех поддерживаемых символов единиц для параметра."""
        p_type = self._norm_param(parameter_type)
        return list(self.parameters[p_type]["units"])

    def get_base_unit(self, parameter_type: str) -> str:
        """Возвращает символ базовой единицы для параметра."""
        p_type = self._norm_param(parameter_type)
        return self.parameters[p_type]["base"]

    # ------ Расширение (динамическое добавление) -----------------
    def add_parameter(self, parameter_type: str, *, base_unit_symbol: str, base_unit_name: str,
                      parameter_name: str) -> None:
        """Добавить новый тип физического параметра."""
        p = self._norm_param(parameter_type)
        if p in self.parameters:
            raise ValueError(f"Параметр '{parameter_type}' уже существует")
        self.parameters[p] = {
            "name": parameter_name,
            "base": base_unit_symbol,
            "units": {
                base_unit_symbol: {
                    "name": base_unit_name,
                    "to_base": lambda v: v,
                    "from_base": lambda v: v,
                }
            },
        }

    def add_unit(self, parameter_type: str, *, unit_symbol: str, unit_name: str,
                 to_base: FactorOrFunc, from_base: FactorOrFunc | None = None) -> None:
        """Добавить новую единицу к существующему параметру."""
        p_type = self._norm_param(parameter_type)
        if p_type not in self.parameters:
            raise UnknownParameterError(p_type)

        if not callable(to_base):
            to_base_func = lambda v, f=float(to_base): v * f
        else:
            to_base_func = to_base

        if from_base is None:
            if callable(to_base):
                raise ValueError("`from_base` обязателен для нелинейных конверсий.")
            from_base = 1.0 / float(to_base)

        if not callable(from_base):
            from_base_func = lambda v, f=float(from_base): v * f
        else:
            from_base_func = from_base

        self.parameters[p_type]["units"][unit_symbol] = {
            "name": unit_name,
            "to_base": to_base_func,
            "from_base": from_base_func,
        }

    # ---------------------- INTERNAL -----------------------------
    @staticmethod
    def _norm_param(p: str) -> str:
        return p.strip().lower()

    def _get_unit(self, parameter_type: str, unit_symbol: str) -> Dict[str, Any]:
        if parameter_type not in self.parameters:
            raise UnknownParameterError(parameter_type)
        units_dict = self.parameters[parameter_type]["units"]
        if unit_symbol not in units_dict:
            raise UnknownUnitError(f"Единица '{unit_symbol}' не найдена для параметра '{parameter_type}'.")
        return units_dict[unit_symbol]

    # ------------------- Инициализация по умолчанию ----------------------
    def _build_defaults(self) -> None:
        """
        Инициализация параметров и единиц "из коробки" согласно требованиям.
        Базовые единицы выбраны в соответствии с вашим списком.
        """
        # P - Давление
        self.add_parameter("pressure", parameter_name="Давление",
                           base_unit_symbol="кгс/см²",
                           base_unit_name="Килограмм-сила на квадратный сантиметр (техническая атмосфера)")
        self.add_unit("pressure", unit_symbol="ат", unit_name="Техническая атмосфера", to_base=1.0, from_base=1.0)
        self.add_unit("pressure", unit_symbol="Па", unit_name="Паскаль",
                      to_base=1.0 / const.KGF_PER_CM2_TO_PA,
                      from_base=const.KGF_PER_CM2_TO_PA)
        self.add_unit("pressure", unit_symbol="кПа", unit_name="Килопаскаль",
                      to_base=1000 / const.KGF_PER_CM2_TO_PA,
                      from_base=const.KGF_PER_CM2_TO_PA / 1000)
        self.add_unit("pressure", unit_symbol="МПа", unit_name="Мегапаскаль",
                      to_base=1_000_000 / const.KGF_PER_CM2_TO_PA,
                      from_base=const.KGF_PER_CM2_TO_PA / 1_000_000)
        self.add_unit("pressure", unit_symbol="бар", unit_name="Бар",
                      to_base=const.BAR_TO_PA / const.KGF_PER_CM2_TO_PA,
                      from_base=const.KGF_PER_CM2_TO_PA / const.BAR_TO_PA)
        self.add_unit("pressure", unit_symbol="атм", unit_name="Физическая атмосфера",
                      to_base=const.ATM_TO_PA / const.KGF_PER_CM2_TO_PA,
                      from_base=const.KGF_PER_CM2_TO_PA / const.ATM_TO_PA)
        self.add_unit("pressure", unit_symbol="мм рт. ст.", unit_name="Миллиметр ртутного столба",
                      to_base=const.MM_HG_TO_PA / const.KGF_PER_CM2_TO_PA,
                      from_base=const.KGF_PER_CM2_TO_PA / const.MM_HG_TO_PA)

        # T - Температура
        self.add_parameter("temperature", parameter_name="Температура",
                           base_unit_symbol="°C", base_unit_name="Градус Цельсия")
        self.add_unit("temperature", unit_symbol="K", unit_name="Кельвин",
                      to_base=lambda v: v - const.CELSIUS_TO_KELVIN_OFFSET,  # K -> °C
                      from_base=lambda v: v + const.CELSIUS_TO_KELVIN_OFFSET)  # °C -> K

        # H - Удельная энтальпия
        self.add_parameter("specific_enthalpy", parameter_name="Удельная энтальпия",
                           base_unit_symbol="ккал/кг", base_unit_name="Килокалория на килограмм")
        self.add_unit("specific_enthalpy", unit_symbol="кДж/кг", unit_name="Килоджоуль на килограмм",
                      to_base=1.0 / const.CAL_TO_J,  # кДж -> ккал
                      from_base=const.CAL_TO_J)
        self.add_unit("specific_enthalpy", unit_symbol="Дж/кг", unit_name="Джоуль на килограмм",
                      to_base=1.0 / (const.CAL_TO_J * 1000),
                      from_base=const.CAL_TO_J * 1000)

        # S - Удельная энтропия
        self.add_parameter("specific_entropy", parameter_name="Удельная энтропия",
                           base_unit_symbol="ккал/кг·K", base_unit_name="Килокалория на килограмм-Кельвин")
        self.add_unit("specific_entropy", unit_symbol="кДж/кг·K", unit_name="Килоджоуль на килограмм-Кельвин",
                      to_base=1.0 / const.CAL_TO_J,
                      from_base=const.CAL_TO_J)

        # v - Удельный объем
        self.add_parameter("specific_volume", parameter_name="Удельный объем",
                           base_unit_symbol="м³/кг", base_unit_name="Кубический метр на килограмм")

        # ρ - Плотность
        self.add_parameter("density", parameter_name="Плотность",
                           base_unit_symbol="кг/м³", base_unit_name="Килограмм на кубический метр")
        self.add_unit("density", unit_symbol="г/см³", unit_name="Грамм на кубический сантиметр",
                      to_base=1000.0, from_base=0.001)

        # N - Мощность
        self.add_parameter("power", parameter_name="Мощность",
                           base_unit_symbol="МВт", base_unit_name="Мегаватт")
        self.add_unit("power", unit_symbol="кВт", unit_name="Киловатт", to_base=0.001, from_base=1000.0)
        self.add_unit("power", unit_symbol="Вт", unit_name="Ватт", to_base=1.0e-6, from_base=1.0e6)
        self.add_unit("power", unit_symbol="л.с.", unit_name="Метрическая лошадиная сила",
                      to_base=const.HP_TO_W / 1.0e6,  # л.с. -> Вт -> МВт
                      from_base=1.0e6 / const.HP_TO_W)

        # G - Массовый расход
        self.add_parameter("mass_flow_rate", parameter_name="Массовый расход",
                           base_unit_symbol="т/ч", base_unit_name="Тонна в час")
        self.add_unit("mass_flow_rate", unit_symbol="кг/с", unit_name="Килограмм в секунду",
                      to_base=1.0 / const.T_PER_H_TO_KG_PER_S,  # кг/с -> т/ч
                      from_base=const.T_PER_H_TO_KG_PER_S)
        self.add_unit("mass_flow_rate", unit_symbol="кг/ч", unit_name="Килограмм в час",
                      to_base=0.001, from_base=1000.0)

        # Q - Тепловая мощность (тепловой поток)
        self.add_parameter("heat_power", parameter_name="Тепловая мощность",
                           base_unit_symbol="Гкал/ч", base_unit_name="Гигакалория в час")
        # 1 Гкал/ч = 10^9 кал/ч = 10^9 * 4.1868 Дж / 3600 с = 1.163 МВт
        GCAL_H_TO_MW = (1.0e9 * const.CAL_TO_J) / 3600 / 1.0e6
        self.add_unit("heat_power", unit_symbol="МВт", unit_name="Мегаватт (тепловой)",
                      to_base=GCAL_H_TO_MW,
                      from_base=1.0 / GCAL_H_TO_MW)
        self.add_unit("heat_power", unit_symbol="кВт", unit_name="Киловатт (тепловой)",
                      to_base=GCAL_H_TO_MW / 1000.0,
                      from_base=1000.0 / GCAL_H_TO_MW)

        # X, Y - Степень сухости / влажности
        self.add_parameter("dryness_fraction", parameter_name="Степень сухости",
                           base_unit_symbol="%", base_unit_name="Проценты")
        self.add_unit("dryness_fraction", unit_symbol="доля", unit_name="Доля (0-1)",
                      to_base=lambda v: v * 100.0,  # доля -> %
                      from_base=lambda v: v / 100.0)  # % -> доля
