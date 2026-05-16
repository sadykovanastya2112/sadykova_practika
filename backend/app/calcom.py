import requests
from flask import current_app
from typing import Dict, Any, List

class CalComClient:
    """
    Клиент для взаимодействия с API Cal.com (v2).
    
    Используется для получения доступных слотов и создания бронирований.
    """

    def __init__(self):
        self.api_url = current_app.config['CALCOM_API_URL']
        self.api_key = current_app.config['CALCOM_API_KEY']
        # Используем slug вместо ID (как указано в .env)
        self.event_type_slug = current_app.config['CALCOM_EVENT_TYPE_SLUG']
        self.username = current_app.config.get('CALCOM_USERNAME')

    def _get_headers(self) -> Dict[str, str]:
        """Возвращает стандартные заголовки для запросов к Cal.com API."""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'cal-api-version': '2026-02-25',
        }

    def get_available_slots(self, start_date: str, end_date: str, timezone: str = 'Europe/Moscow') -> List[Dict[str, Any]]:
        """
        Запрашивает доступные слоты для заданного типа события (event type slug).

        Параметры:
            start_date: дата начала в формате YYYY-MM-DD
            end_date: дата окончания в формате YYYY-MM-DD
            timezone: часовой пояс (по умолчанию Europe/Moscow)

        Возвращает список словарей с ключом 'start'.
        """
        params = {
            'eventTypeSlug': self.event_type_slug,   # используем slug, а не ID
            'start': start_date,
            'end': end_date,
            'timeZone': timezone,
            'username': self.username,
        }

        response = requests.get(
            f"{self.api_url}/slots",
            headers=self._get_headers(),
            params=params,
        )

        response.raise_for_status()
        data = response.json()
        # API возвращает слоты в виде { "2024-08-13": ["09:00", "10:00"] }
        slots = []
        for date, times in data.get('data', {}).get('slots', {}).items():
            for time in times:
                slots.append({
                    "start": f"{date}T{time}",
                })
        return slots

    def book_slot(self, start: str, attendee_name: str, attendee_email: str) -> Dict[str, Any]:
        """
        Создаёт бронирование в Cal.com.

        Параметры:
            start: дата и время начала в ISO формате (например, 2025-05-01T10:00:00)
            attendee_name: имя участника (клиента)
            attendee_email: email участника

        Возвращает данные созданного бронирования (содержит uid и id).
        """
        payload = {
            "start": start,
            "eventTypeSlug": self.event_type_slug,   # используем slug
            "attendee": {
                "name": attendee_name,
                "email": attendee_email,
                "timeZone": "Europe/Moscow",
                "username": self.username,
            }
        }

        response = requests.post(
            f"{self.api_url}/bookings",
            headers=self._get_headers(),
            json=payload,
        )
        response.raise_for_status()
        return response.json().get('data')