import requests
import json
import gzip
import schedule
import time

def save_gzip(data, file_path):
    """
    Salva dados em formato JSON compactado.
    """
    with gzip.open(file_path, "wt", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def fetch_google_sheet_as_json(sheet_url, output_file="data.json.gz"):
    try:
        response = requests.get(sheet_url)
        if response.status_code == 200:
            raw_data = response.text.lstrip("/*O_o*/\ngoogle.visualization.Query.setResponse(").rstrip(");")
            data = json.loads(raw_data)
            rows = data['table']['rows']
            headers = [col['label'] for col in data['table']['cols']]
            processed_data = [
                {headers[i]: row['c'][i]['v'] if row['c'][i] else None for i in range(len(headers))}
                for row in rows
            ]

            # Salvar como arquivo compactado
            save_gzip(processed_data, output_file)
            print(f"Data saved to {output_file}")
        else:
            print(f"Error accessing the sheet: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")


sheet_url = "https://docs.google.com/spreadsheets/d/1Ai8mEEoLvMjpooM2zUQvfDYNMy9FwXSWoqMaviL6eGw/gviz/tq?tqx=out:json&headers=1&tq=select+A,C,F,K,L,N,Q,V,AD,AE,AF,AG,AH,AI,AJ,AK,AL,AM,AN,AO,AP,AQ,AR,AS,AT,AU+where+C+is+not+null"


def run_weekly():
    print("Updating sheet data...")
    fetch_google_sheet_as_json(sheet_url, output_file="weekly_data.json.gz")


schedule.every().week.do(run_weekly)

if __name__ == "__main__":
    print("Script started. Waiting for the next scheduled execution...")
    while True:
        schedule.run_pending()
        time.sleep(1)
