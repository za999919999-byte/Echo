from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from parse_hitmos.entered_tracks import EnteredTrack
import requests
import time
from urllib.parse import quote
import ssl
import requests
from urllib3.poolmanager import PoolManager

# Временно отключаем проверку SSL (только для диагностики!)
requests.packages.urllib3.disable_warnings()
ssl._create_default_https_context = ssl._create_unverified_context

app = Flask(__name__)
CORS(app)

@app.route('/search')
def search():
    query = request.args.get('q')
    limit = int(request.args.get('limit', 48))
    
    if limit > 48:
        limit = 48
    
    if not query:
        return jsonify({"error": "Missing query"}), 400
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = EnteredTrack(query, limit)
            data = result.get_all
            items = data.get('items', [])
            
            formatted_tracks = []
            for track in items:
                url_down = track.get('url_down', '')
                full_download_url = f"https://ru.hitmoz.org{url_down}" if url_down else None
                
                formatted_tracks.append({
                    "id": track.get('url_track'),
                    "title": track.get('title'),
                    "artist": track.get('author'),
                    "duration": track.get('duration_track'),
                    "artwork": track.get('picture_url'),
                    "download_url": full_download_url,
                    "url_down": url_down  # <- Для скачивания через наш прокси
                })
            
            return jsonify(formatted_tracks)
            
        except Exception as e:
            print(f"[ATTEMPT {attempt + 1}/{max_retries}] Error: {e}")
            if attempt < max_retries - 1:
                time.sleep(3)
                continue
            return jsonify({"error": str(e)}), 500

@app.route('/download')
def download():
    url_down = request.args.get('url_down')
    if not url_down:
        return jsonify({"error": "Missing url_down parameter"}), 400
    
    try:
        full_url = f"https://ru.hitmoz.org{url_down}"
        
        # Максимальная эмуляция браузера
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
            'Accept': 'audio/webm,audio/ogg,audio/wav,audio/*;q=0.9,application/ogg;q=0.7,video/*;q=0.6,*/*;q=0.5',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'identity',
            'Referer': 'https://ru.hitmoz.org/',
            'Origin': 'https://ru.hitmoz.org',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'audio',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        
        session = requests.Session()
        # Сначала заходим на главную для получения cookies
        session.get('https://ru.hitmoz.org/', headers={'User-Agent': headers['User-Agent']}, timeout=15)
        
        # Затем скачиваем MP3
        mp3_response = session.get(full_url, headers=headers, timeout=30)
        
        if mp3_response.status_code != 200:
            return jsonify({"error": f"Failed to download: {mp3_response.status_code}"}), 500
        
        file_data = mp3_response.content
        
        filename = url_down.split('/')[-1]
        if not filename.endswith('.mp3'):
            filename += '.mp3'
        
        return Response(
            file_data,
            status=200,
            headers={
                'Content-Type': 'audio/mpeg',
                'Content-Length': str(len(file_data)),
                'Content-Disposition': f'attachment; filename="{quote(filename)}"',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'no-cache'
            }
        )
        
    except Exception as e:
        print(f"[DOWNLOAD ERROR] {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/proxy-image')
def proxy_image():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Missing URL"}), 400
    
    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }, timeout=10)
        
        return Response(
            response.content,
            status=200,
            headers={
                'Content-Type': response.headers.get('Content-Type', 'image/jpeg'),
                'Cache-Control': 'public, max-age=86400',
                'Access-Control-Allow-Origin': '*'
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)