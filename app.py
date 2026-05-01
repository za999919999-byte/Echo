from flask import Flask, request, jsonify, Response
import requests
import time
from urllib.parse import quote
from bs4 import BeautifulSoup

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
    if not query:
        return jsonify({"error": "Missing query"}), 400
    
    try:
        # Прямой запрос к hitmoz (без parse_hitmos)
        search_url = f'https://ru.hitmoz.org/search?q={quote(query)}'
        resp = requests.get(search_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        titles = [t.text.strip() for t in soup.find_all("div", class_="track__title")]
        artists = [a.text.strip() for a in soup.find_all("div", class_="track__desc")]
        durations = [d.text.strip() for d in soup.find_all("div", class_="track__fulltime")]
        urls_dow = [u.get('href') for u in soup.find_all('a', class_='track__download-btn')]
        track_urls = [f"https://ru.hitmoz.org{a.get('href')}" for a in soup.find_all('a', class_='track__info-l')]

        tracks = []
        limit = int(request.args.get('limit', min(48, len(titles))))
        for i in range(limit):
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

@app.route('/download')
def download():
    url_down = request.args.get('url_down')
    if not url_down:
        return jsonify({"error": "Missing url_down"}), 400
    try:
        full_url = f"https://ru.hitmoz.org{url_down}"
        mp3 = requests.get(full_url, headers=HEADERS, timeout=30)
        if mp3.status_code != 200:
            return jsonify({"error": f"Download failed: {mp3.status_code}"}), 500
        filename = url_down.split('/')[-1]
        if not filename.endswith('.mp3'):
            filename += '.mp3'
        return Response(mp3.content, content_type='audio/mpeg',
                       headers={'Content-Disposition': f'attachment; filename="{quote(filename)}"'})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/proxy-image')
def proxy_image():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Missing URL"}), 400
    try:
        resp = requests.get(url, headers={'User-Agent': HEADERS['User-Agent']}, timeout=10)
        return Response(resp.content, content_type=resp.headers.get('Content-Type', 'image/jpeg'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
