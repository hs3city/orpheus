import aiocron
import requests
import json
import datetime

class Calendar:

    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.data = self.get_weekly_events()
        self.parse_data()
        self.daily_events = self.update_daily_events(self.data)

    def get_weekly_events(self):
        result = requests.get(
                f"https://teamup.com/ksizm7axps9jy9yb8r/events?startDate={self.start}&endDate={self.end}&tz=Europe/Warsaw"
            )
        return result.json()['events']

    def parse_data(self):
        important_keys = [
                "title", "who", "location", "notes", "start_dt", "end_dt"
                ]
        dates = ["start_dt", "end_dt"]
        parsed_data = []
        for event in self.data:
            parsed_event = dict()
            for key in important_keys:
                if key in dates:
                    bzdura = event[key][:-3] + event[key][-2:]
                    parsed_event[key] = datetime.datetime.strptime(bzdura, "%Y-%m-%dT%H:%M:%S%z")
                else:
                    parsed_event[key] = event[key]

            parsed_data.append(parsed_event)
        self.data = parsed_data

    @staticmethod
    def update_daily_events(data):
        todays_events = []
        weekday = datetime.date.today().isoweekday()
        for event in data:
            if event['start_dt'].isoweekday() == weekday:
                todays_events.append(event)
        return todays_events






