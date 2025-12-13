import os
import sys
import shutil
import yt_dlp
import json
import uuid
import threading
from flask import Flask, render_template, request, jsonify, Response

app = Flask(__name__)
DOWNLOAD_DIR = "downloads"
download_progress = {}

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_opts(use_cookies=False):
    opts = {
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    if use_cookies:
        opts['cookiesfrombrowser'] = ('chrome', 'firefox', 'edge')
    return opts

def get_video_info(url):
    ydl_opts = get_opts(use_cookies=False)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return info
        except Exception as e:
            if "Sign in" in str(e) or "403" in str(e):
                ydl_opts = get_opts(use_cookies=True)
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                        info = ydl2.extract_info(url, download=False)
                        return info
                except Exception:
                    return None
            return None

def extract_qualities(info):
    formats = info.get('formats', [])
    video_qualities = []
    audio_qualities = []
    seen_heights = set()
    seen_abr = set()
    
    for f in formats:
        if f.get('vcodec') != 'none' and f.get('height'):
            height = f['height']
            if height not in seen_heights:
                seen_heights.add(height)
                video_qualities.append({
                    'height': height,
                    'label': f'{height}p',
                    'format_id': f['format_id']
                })
        
        if f.get('acodec') != 'none' and f.get('abr'):
            abr = int(f['abr'])
            if abr not in seen_abr:
                seen_abr.add(abr)
                audio_qualities.append({
                    'abr': abr,
                    'label': f'{abr} kbps',
                    'format_id': f['format_id']
                })
    
    video_qualities.sort(key=lambda x: x['height'], reverse=True)
    audio_qualities.sort(key=lambda x: x['abr'], reverse=True)
    
    return video_qualities, audio_qualities

def progress_hook(d, download_id):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
        downloaded = d.get('downloaded_bytes', 0)
        percent = (downloaded / total * 100) if total > 0 else 0
        download_progress[download_id] = {
            'status': 'downloading',
            'percent': round(percent, 1),
            'speed': d.get('speed', 0),
            'eta': d.get('eta', 0)
        }
    elif d['status'] == 'finished':
        download_progress[download_id] = {
            'status': 'processing',
            'percent': 100,
            'message': 'Processing file...'
        }

def perform_download(url, mode, quality, download_id):
    ensure_dir(DOWNLOAD_DIR)
    ydl_opts = get_opts(use_cookies=False)
    ydl_opts['progress_hooks'] = [lambda d: progress_hook(d, download_id)]
    
    try:
        if mode == 'video_best':
            ydl_opts['outtmpl'] = f'{DOWNLOAD_DIR}/%(title)s - %(height)sp.%(ext)s'
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
        
        elif mode == 'video_quality':
            ydl_opts['outtmpl'] = f'{DOWNLOAD_DIR}/%(title)s - {quality}p.%(ext)s'
            ydl_opts['format'] = f'bestvideo[height={quality}]+bestaudio/best[height={quality}]'
        
        elif mode == 'audio_best':
            ydl_opts['outtmpl'] = f'{DOWNLOAD_DIR}/%(title)s.%(ext)s'
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }]
        
        elif mode == 'audio_quality':
            ydl_opts['outtmpl'] = f'{DOWNLOAD_DIR}/%(title)s - {quality}kbps.%(ext)s'
            ydl_opts['format'] = f'bestaudio[abr<={quality}]/bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': str(quality),
            }]
        
        elif mode == 'playlist':
            info = get_video_info(url)
            if info and 'entries' in info:
                playlist_title = info.get('title', 'Playlist')
                safe_title = "".join([c for c in playlist_title if c.isalpha() or c.isdigit() or c==' ']).strip()
                if not safe_title:
                    safe_title = "Playlist"
                playlist_dir = os.path.join(DOWNLOAD_DIR, safe_title)
                ensure_dir(playlist_dir)
                
                ydl_opts['outtmpl'] = f'{playlist_dir}/%(playlist_index)s - %(title)s.%(ext)s'
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if mode == 'playlist':
            if os.path.exists(playlist_dir):
                files_in_dir = os.listdir(playlist_dir)
                if files_in_dir:
                    shutil.make_archive(playlist_dir, 'zip', playlist_dir)
                    shutil.rmtree(playlist_dir)
        
        download_progress[download_id] = {
            'status': 'complete',
            'percent': 100,
            'message': 'Download complete!'
        }
    
    except Exception as e:
        if "403" in str(e) or "Sign in" in str(e):
            ydl_opts['cookiesfrombrowser'] = ('chrome', 'firefox', 'edge')
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                download_progress[download_id] = {
                    'status': 'complete',
                    'percent': 100,
                    'message': 'Download complete!'
                }
            except Exception as e2:
                download_progress[download_id] = {
                    'status': 'error',
                    'message': str(e2)
                }
        else:
            download_progress[download_id] = {
                'status': 'error',
                'message': str(e)
            }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/info', methods=['POST'])
def get_info():
    data = request.json
    url = data.get('url', '')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    info = get_video_info(url)
    if not info:
        return jsonify({'error': 'Could not fetch video info'}), 400
    
    is_playlist = 'entries' in info
    video_qualities, audio_qualities = [], []
    
    if not is_playlist:
        video_qualities, audio_qualities = extract_qualities(info)
    else:
        entries = list(info.get('entries', []))
        playlist_count = len(entries)
        return jsonify({
            'title': info.get('title', 'Unknown'),
            'is_playlist': True,
            'count': playlist_count,
            'thumbnail': info.get('thumbnails', [{}])[-1].get('url', '') if info.get('thumbnails') else ''
        })
    
    return jsonify({
        'title': info.get('title', 'Unknown'),
        'thumbnail': info.get('thumbnail', ''),
        'duration': info.get('duration', 0),
        'channel': info.get('channel', info.get('uploader', 'Unknown')),
        'is_playlist': False,
        'video_qualities': video_qualities,
        'audio_qualities': audio_qualities
    })

@app.route('/api/download', methods=['POST'])
def start_download():
    data = request.json
    url = data.get('url', '')
    mode = data.get('mode', 'video_best')
    quality = data.get('quality', '')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    download_id = str(uuid.uuid4())
    download_progress[download_id] = {
        'status': 'starting',
        'percent': 0
    }
    
    thread = threading.Thread(target=perform_download, args=(url, mode, quality, download_id))
    thread.start()
    
    return jsonify({'download_id': download_id})

@app.route('/api/progress/<download_id>')
def get_progress(download_id):
    def generate():
        while True:
            if download_id in download_progress:
                progress = download_progress[download_id]
                yield f"data: {json.dumps(progress)}\n\n"
                if progress.get('status') in ['complete', 'error']:
                    break
            else:
                yield f"data: {json.dumps({'status': 'waiting', 'percent': 0})}\n\n"
            import time
            time.sleep(0.5)
    
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    ensure_dir(DOWNLOAD_DIR)
    app.run(debug=True, port=5000, threaded=True)