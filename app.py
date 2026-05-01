from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "Missing query"}), 400
    
    try:
        # Простой тестовый ответ
        return jsonify([
            {
                "id": "test1",
                "title": f"Результат для: {query}",
                "artist": "Тестовый исполнитель",
                "duration": "3:45",
                "artwork": "",
                "download_url": "",
                "url_down": ""
            }
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
