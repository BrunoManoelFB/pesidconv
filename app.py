from flask import Flask, jsonify, request, render_template
import requests
import json
import os
import re
import gzip
import threading
import http.server
import socketserver


app = Flask(__name__)

# URL pública para o gviz JSON
SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/1Ai8mEEoLvMjpooM2zUQvfDYNMy9FwXSWoqMaviL6eGw/gviz/tq?"
    "tqx=out:json&headers=1&tq=select+A,C,F,K,L,N,Q,V,AD,AE,AF,AG,AH,AI,AJ,AK,AL,AM,AN,AO,AP,AQ,AR,AS,AT,AU+where+C+is+not+null"
)

# Nome do arquivo local para salvar o JSON compactado
LOCAL_JSON_FILE = "google_sheet_data.json.gz"


def save_gzip(data, file_path):
    """
    Salva dados em formato JSON compactado.
    """
    with gzip.open(file_path, "wt", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def load_gzip(file_path):
    """
    Carrega dados de um arquivo JSON compactado.
    """
    with gzip.open(file_path, "rt", encoding="utf-8") as f:
        return json.load(f)


@app.route("/update-json", methods=["GET"])
def fetch_and_save_google_sheet():
    """
    Faz o download da planilha do Google Sheets no formato gviz JSON,
    processa, salva localmente (compactado) e retorna o JSON formatado.
    """
    try:
        response = requests.get(SHEET_URL)
        if response.status_code == 200:
            raw_data = response.text.lstrip("/*O_o*/\ngoogle.visualization.Query.setResponse(").rstrip(");")
            data = json.loads(raw_data)
            rows = data['table']['rows']
            headers = [col['label'] for col in data['table']['cols']]
            processed_data = []

            for row in rows:
                row_data = {}
                for i, cell in enumerate(row['c']):
                    if cell:
                        value = cell['v']
                        if isinstance(value, str):
                            value = re.split(r"\n|\r", value)[0]
                        row_data[headers[i]] = value
                processed_data.append(row_data)

            # Salvar JSON compactado
            save_gzip(processed_data, LOCAL_JSON_FILE)
            return jsonify({"message": "JSON updated and saved successfully!"}), 200
        else:
            return jsonify({"error": f"Error accessing the sheet: {response.status_code}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get-local-json", methods=["GET"])
def get_local_json():
    """
    Retorna o JSON salvo localmente (compactado).
    """
    if os.path.exists(LOCAL_JSON_FILE):
        try:
            data = load_gzip(LOCAL_JSON_FILE)
            return jsonify(data), 200
        except Exception as e:
            return jsonify({"error": f"Failed to read compressed JSON: {e}"}), 500
    else:
        return jsonify({"error": "Local JSON not found. Update data using /update-json."}), 404


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/health")
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route("/search", methods=["POST"])
def search():
    try:
        player_id = float(request.form.get("player_id"))
        converted_id = None
        message = None

        if player_id > 25165824:
            converted_id = player_id - 25165824
            message = f"Unlicensed AFC Champions League ID. Its base ID is {converted_id}."
        elif player_id > 16777216:
            converted_id = player_id - 16777216
            message = f"Licensed AFC Champions League ID. Its base ID is {converted_id}."
        elif player_id > 8388608:
            converted_id = player_id - 8388608
            message = f"Unlicensed eFootball ID. Its base ID is {converted_id}."
        else:
            message = "Invalid ID. Please enter a valid player ID."

        player = None
        if os.path.exists(LOCAL_JSON_FILE) and converted_id:
            players = load_gzip(LOCAL_JSON_FILE)
            print(f"Converted ID: {converted_id}")  # Log do ID convertido
            print(f"Players loaded: {len(players)} records")  # Log do número de registros

            # Debug: Exibir os 5 primeiros registros para inspeção
            for p in players[:5]:
                print(f"Player data: {p}")

            # Certifique-se de que o ID no JSON é comparado corretamente
            player = next(
                (p for p in players if int(float(p.get("Lic. ID:", 0))) == int(converted_id)),
                None
            )

        print(f"Player found: {player}")  # Log do jogador encontrado
        return render_template("result.html", player=player, player_id=player_id, message=message)
    except ValueError:
        return render_template("result.html", error="Invalid player ID")



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
