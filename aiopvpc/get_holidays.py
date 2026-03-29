import json
import requests
from datetime import date, datetime


class Holiday:
    def __init__(self, anno: int):
        self.anno = anno

    def week_holidays(self, number_day):
        days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        return days[number_day]

    def get_holidays(self) -> dict[int, dict[date, str]]:
        anno_dic = {}
        response = requests.get(
            f'https://date.nager.at/api/v3/PublicHolidays/{self.anno}/ES',
            timeout=5
        )

        if response.status_code != 200:
            return {}

        holidays_dic: dict[date, str] = {}
        for holiday in json.loads(response.text):
            if not holiday['global']:
                continue
            fecha = date.fromisoformat(holiday['date'])
            if fecha.isoweekday() >= 6:  # Fines de semana ya son P3
                continue
            day_name = self.week_holidays(fecha.weekday())
            holidays_dic[fecha] = f"({day_name}), {holiday['localName']}"

        return {self.anno: holidays_dic}

    @staticmethod
    def convert_string_to_date(string_date):
        return datetime.strptime(string_date, "%Y-%m-%d")




