from flask import Flask, request, jsonify, Response
import requests
from urllib.parse import quote

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,ngrok-skip-browser-warning'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
}

@app.route('/search')
def search():
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 48))
    if not query:
        return jsonify({"error": "Missing query"}), 400
    
    try:
        # Используем прокси для обхода блокировки
        hitmoz_url = f'https://ru.hitmoz.org/search?q={quote(query)}'
        proxy_url = f'https://api.allorigins.win/raw?url={quote(hitmoz_url)}'
        
        resp = requests.get(proxy_url, headers=HEADERS, timeout=15)
        
        # Парсим HTML
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        titles = [t.text.strip() for t in soup.find_all("div", class_="track__title")]
        artists = [a.text.strip() for a in soup.find_all("div", class_="track__desc")]
        durations = [d.text.strip() for d in soup.find_all("div", class_="track__fulltime")]
        urls_dow = [u.get('href') for u in soup.find_all('a', class_='track__download-btn')]
        track_urls = [f"https://ru.hitmoz.org{a.get('href')}" for a in soup.find_all('a', class_='track__info-l')]

        tracks = []
        count = min(limit, len(titles))
        for i in range(count):
            tracks.append({
                "id": track_urls[i] if i < len(track_urls) else f"track_{i}",
                "title": titles[i] if i < len(titles) else "Без названия",
                "artist": artists[i] if i < len(artists) else "Неизвестен",
                "duration": durations[i] if i < len(durations) else "00:00",
                "artwork": "",
                "download_url": f"https://ru.hitmoz.org{urls_dow[i]}" if i < len(urls_dow) and urls_dow[i] else None,
                "url_down": urls_dow[i] if i < len(urls_dow) else ""
            })
        return jsonify(tracks)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Остальные маршруты (download, proxy-image) оставьте как есть

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
