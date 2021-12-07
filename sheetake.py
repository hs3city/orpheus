import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def auth():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_console()
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

class Worksheet:
    def __init__(self, creds, spreadsheet_id, sheet_name):
        self.creds = creds
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.service = build('sheets', 'v4', credentials=self.creds)

    def update_values(self):
        # Call the Sheets API
        sheet = self.service.spreadsheets()
        result = sheet.values().get(spreadsheetId=self.spreadsheet_id,
                                    range=self.sheet_name).execute()
        self.values = result.get('values', [])

    def get_users(self):
        """
        Remember to call `update_values()` before calling this one!
        """
        users = [x.strip() for x in self.values[1][2:]]

        return users

    def get_training_links(self):
        """
        Remember to call `update_values()` before calling this one!
        """
        training_links = dict()
        for i, row in enumerate(self.values[2:]):
            training_links[row[0]] = [row[1], i]

        return training_links

    def mark_done(self, x, y, payload):
        service = build('sheets', 'v4', credentials=self.creds)

        # Call the Sheets API
        body = {
                "values": [[payload],]
                }
        sheet = service.spreadsheets()
        result = sheet.values().update(spreadsheetId=self.spreadsheet_id,
                range=f"{parse_col(x)}{y}:{parse_col(x)}{y}", valueInputOption='RAW', body=body).execute()

def parse_col(x):
    asc_ord = ord('A')
    return chr(asc_ord+x)


def main():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """

    creds = auth()

    values = get_sheet_done(creds)

    if not values:
        print('No data found.')
    else:
        for row in values[2:]:
            print(row)
            date = row[0]
            movie = row[1]

if __name__ == '__main__':
    main()
