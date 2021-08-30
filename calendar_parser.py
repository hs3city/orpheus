import aiocron
import requests
import json
import datetime

class Calendar:

    def __init__(self, start, end, client):
        self.start = start
        self.end = end
        self.client = client
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

    # TODO: This has to be formatted properly, some kind of template introduction?
    async def send_daily_event_schedule(self):
        events = []
        for event in self.daily_events:
            text = f"""
            Event name: {event['title']}
            Event description {event['notes']}
            Event start: {event['start_dt']}"""
            events.append(text)

        await self.client.get_channel(806843548225634335).send("\n".join(events))

    async def send_weekly_event_schedule(self):
        weekdays = ['\nPoniedzialek', '\nWtorek', '\nSroda', '\nCzwartek', '\nPiatek', '\nSobota', '\nNiedziela']
        events = ["-",]
        event_timeline = sorted(self.data, key=lambda x: x['start_dt'])
        days = []
        for event in event_timeline:
            if event['start_dt'].isoweekday() not in days:
                days.append(event['start_dt'].isoweekday())
                events.append(f"{weekdays[event['start_dt'].weekday()]}")
            text = f"""
            Event name: {event['title']}
            Event description {event['notes']}
            Event start: {event['start_dt']}"""
            events.append(text)

        await self.client.get_channel(806843548225634335).send("\n".join(events))

    async def send_reminder(self):
        events_in_quarter = ["-"]
        for event in self.daily_events:
            if datetime.datetime.now().astimezone() + datetime.timedelta(minutes=15) > event['start_dt'] and datetime.datetime.now().astimezone() < event['start_dt']:
                events_in_quarter.append(f"{event['title']} zaczyna sie juz za 15 minut")
        await self.client.get_channel(806843548225634335).send("\n".join(events_in_quarter))


    @staticmethod
    def update_daily_events(data):
        todays_events = [{"title": "Test 1", "start_dt": datetime.datetime.now().astimezone() + datetime.timedelta(minutes=15)},{"title": "Test 2", "start_dt": datetime.datetime.now().astimezone() + datetime.timedelta(minutes=15)}]
        weekday = datetime.date.today().isoweekday()
        weekday = 3
        for event in data:
            if event['start_dt'].isoweekday() == weekday:
                todays_events.append(event)
        return todays_events

