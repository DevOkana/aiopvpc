import json
import urllib.request
from datetime import date, datetime


class Holiday:
    def __init__(self, anno: int):
        self.anno = anno

    def week_holidays(self, number_day):
        days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        return days[number_day]

    def get_holidays(self) -> dict[int, dict[date, str]]:
        url = f'https://date.nager.at/api/v3/PublicHolidays/{self.anno}/ES'
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                holidays_dic: dict[date, str] = {}
                for holiday in json.loads(response.read().decode()):
                    if not holiday['global']:
                        continue
                    fecha = date.fromisoformat(holiday['date'])
                    if fecha.isoweekday() >= 6:
                        continue
                    day_name = self.week_holidays(fecha.weekday())
                    holidays_dic[fecha] = f"({day_name}), {holiday['localName']}"
                return {self.anno: holidays_dic}
        except Exception:
            return {}