"""ESIOS API handler for HomeAssistant. PVPC tariff periods."""

from __future__ import annotations

import concurrent.futures
from datetime import date, datetime, timedelta

import holidays


class _LazyHolidayDict:
    """
    Lazy-loaded dict of Spanish national holidays (lunes-viernes only).

    Rules applied:
    - Only national holidays (ES, no subdivision/region).
    - Weekends excluded: already treated as P3 by isoweekday logic.
    - 'Observed' (trasladados) excluded: a working Monday should NOT become
      P3 just because the original holiday fell on a Sunday.
      The PVPC tariff uses the canonical holiday date, not the substitution.
    """
    def __init__(self) -> None:
        self._cache: dict[int, dict[date, str]] = {}
        self.es_holidays: dict[int, dict[date, str]] = {}

    def __getitem__(self, year: int) -> dict[date, str]:
        if year not in self._cache:
            with concurrent.futures.ThreadPoolExecutor() as pool:
                raw: holidays.HolidayBase = pool.submit(
                    lambda: holidays.ES(
                        years=year,
                        observed=False,   # No trasladados
                    )
                ).result()
            # Filter: keep only Mon-Fri (isoweekday 1-5)
            # Weekends are already P3 by tariff logic, no need to include them.
            self._cache[year] = {
                d: name
                for d, name in raw.items()
                if d.isoweekday() <= 5  # 1=Mon ... 5=Fri, 6=Sat, 7=Sun
            }
        return self._cache[year]

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, date):
            return False
        return key in self[key.year]

_HOURS_P2 = (8, 9, 14, 15, 16, 17, 22, 23)
_HOURS_P2_CYM = (8, 9, 10, 15, 16, 17, 18, 23)
_NATIONAL_EXTRA_HOLIDAYS_FOR_P3_PERIOD = _LazyHolidayDict()


def _tariff_period_key(local_ts: datetime, zone_ceuta_melilla: bool) -> str:
    """Return period key (P1/P2/P3) for current hour."""
    day = local_ts.date()
    national_holiday = day in _NATIONAL_EXTRA_HOLIDAYS_FOR_P3_PERIOD[day.year]
    if national_holiday or day.isoweekday() >= 6 or local_ts.hour < 8:
        return "P3"
    if zone_ceuta_melilla and local_ts.hour in _HOURS_P2_CYM:
        return "P2"
    if not zone_ceuta_melilla and local_ts.hour in _HOURS_P2:
        return "P2"
    return "P1"


def get_current_and_next_tariff_periods(
    local_ts: datetime, zone_ceuta_melilla: bool
) -> tuple[str, str, timedelta]:
    """Get tariff periods for PVPC 2.0TD."""
    current_period = _tariff_period_key(local_ts, zone_ceuta_melilla)
    delta = timedelta(hours=1)
    while (
        next_period := _tariff_period_key(local_ts + delta, zone_ceuta_melilla)
    ) == current_period:
        delta += timedelta(hours=1)
    return current_period, next_period, delta
