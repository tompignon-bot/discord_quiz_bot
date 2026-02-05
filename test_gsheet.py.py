Python 3.14.2 (tags/v3.14.2:df79316, Dec  5 2025, 17:18:21) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
>>> 
>>> import json
... import gspread
... import os
... 
... SHEET_JSON = os.environ["GOOGLE_CREDS_JSON"]
... SHEET_ID = os.environ["SHEET_ID"]
... 
... creds_dict = json.loads(SHEET_JSON)
... client = gspread.service_account_from_dict(creds_dict)
... sheet = client.open_by_key(SHEET_ID).sheet1
... 
... # Affiche juste la première ligne pour tester
... print("✅ Connexion réussie ! Premier enregistrement :")
... print(sheet.get_all_records()[:1])
