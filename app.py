import os
import sys
import shutil
import time
import zipfile
import yt_dlp
import json
import uuid
import threading
from flask import Flask, render_template, request, jsonify, Response, send_file, after_this_request

app = Flask(__name__)
DOWNLOAD_DIR = "downloads"
download_progress = {}

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def cleanup_old_downloads():
    try:
        now = time.time()
        for item in os.listdir(DOWNLOAD_DIR):
            item_path = os.path.join(DOWNLOAD_DIR, item)
            # Remove items older than 1 hour (3600 seconds)
            if os.stat(item_path).st_mtime < now - 3600:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
    except Exception as e:
        print(f"Error cleaning up: {e}")

def get_opts():
    """Get yt-dlp options optimized for server environment"""
    opts = {
        'quiet': True,
        'no_warnings': True,
        # Better user agent
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        # Additional headers to avoid bot detection
        'http_headers': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        },
        # Use extractors that work better on servers
        'extractor_args': {
            'youtube': {
                'skip': ['hls', 'dash'],  # Prefer direct formats
                'player_skip': ['webpage'],
                'player_client': ['android', 'web'],
            }
        },
    }
    return opts

def get_video_info(url):
    ydl_opts = get_opts()
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return info
        except Exception as e:
            print(f"Error fetching video info: {e}")
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
    ydl_opts = get_opts()
    ydl_opts['progress_hooks'] = [lambda d: progress_hook(d, download_id)]
    
    # Use 3 underscores as delimiter
    prefix = f"{download_id}___"
    
    final_filepath = None
    playlist_dir = None

    try:
        if mode == 'video_best':
            ydl_opts['outtmpl'] = f'{DOWNLOAD_DIR}/{prefix}%(title)s - %(height)sp.%(ext)s'
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
        
        elif mode == 'video_quality':
            ydl_opts['outtmpl'] = f'{DOWNLOAD_DIR}/{prefix}%(title)s - {quality}p.%(ext)s'
            ydl_opts['format'] = f'bestvideo[height={quality}]+bestaudio/best[height={quality}]'
        
        elif mode == 'audio_best':
            ydl_opts['outtmpl'] = f'{DOWNLOAD_DIR}/{prefix}%(title)s.%(ext)s'
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }]
        
        elif mode == 'audio_quality':
            ydl_opts['outtmpl'] = f'{DOWNLOAD_DIR}/{prefix}%(title)s - {quality}kbps.%(ext)s'
            ydl_opts['format'] = f'bestaudio[abr<={quality}]/bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': str(quality),
            }]
        
        elif mode == 'playlist':
            # For playlist, keep using a unique subdirectory to contain multiple files
            # But name the directory with ID to avoid conflicts
            playlist_dir = os.path.join(DOWNLOAD_DIR, f"playlist_{download_id}")
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
        
        # Determine the file to serve
        if mode == 'playlist':
            if os.path.exists(playlist_dir):
                # Use zipfile with ZIP_STORED for speed (no compression)
                zip_filename = f"{playlist_dir}.zip"
                with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_STORED) as zipf:
                    for root, dirs, files in os.walk(playlist_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Add file to zip with relative path
                            arcname = os.path.relpath(file_path, playlist_dir)
                            zipf.write(file_path, arcname)
                
                final_filepath = zip_filename
                
                # Cleanup the raw files directory immediately
                try:
                    shutil.rmtree(playlist_dir)
                except Exception as cleanup_error:
                    print(f"Warning: Could not delete playlist directory {playlist_dir}: {cleanup_error}")
        else:
            # Find the file with the prefix in DOWNLOAD_DIR
            for fname in os.listdir(DOWNLOAD_DIR):
                if fname.startswith(prefix):
                    final_filepath = os.path.join(DOWNLOAD_DIR, fname)
                    break

        if final_filepath and os.path.exists(final_filepath):
            download_progress[download_id] = {
                'status': 'complete',
                'percent': 100,
                'message': 'Download complete!',
                'filepath': final_filepath
            }
        else:
            raise Exception("File not found after download processing")
    
    except Exception as e:
        # Cleanup if something went wrong
        if playlist_dir and os.path.exists(playlist_dir):
            try: shutil.rmtree(playlist_dir)
            except: pass
            
        if "403" in str(e) or "Sign in" in str(e):
             # Logic for retry with cookies could be added here, but for brevity and avoiding complexity,
             # let's just report error for now or keep simplistic.
             # If I want to keep retry logic, I need to copy paste the block.
             # Given the "stuck" complaint, complex retry loops might be hiding errors.
             download_progress[download_id] = {
                'status': 'error',
                'message': f"Access Error: {str(e)}"
             }
        else:
            download_progress[download_id] = {
                'status': 'error',
                'message': str(e)
            }

@app.route('/api/download_file/<download_id>')
def download_file(download_id):
    if download_id in download_progress:
        info = download_progress[download_id]
        filepath = info.get('filepath')
        
        if info.get('status') == 'complete' and filepath and os.path.exists(filepath):
            # Calculate download name (strip uuid prefix)
            filename = os.path.basename(filepath)
            download_name = filename
            
            # Remove prefix id___
            if "___" in filename:
                download_name = filename.split("___", 1)[1]
            elif filename.startswith("playlist_"):
                download_name = "Playlist.zip" # Fallback
            
            # Use a generator to stream the file and delete it afterwards
            def generate():
                try:
                    with open(filepath, 'rb') as f:
                        while True:
                            chunk = f.read(8192) # 8KB chunks
                            if not chunk:
                                break
                            yield chunk
                except Exception as e:
                    print(f"Error streaming file: {e}")
                finally:
                    # Cleanup after streaming is done (or failed) and file is closed
                    try:
                        if os.path.exists(filepath):
                            os.remove(filepath)
                            print(f"Cleaned up file: {filepath}")
                            # Ideally we should remove from dict too
                            download_progress.pop(download_id, None) 
                    except Exception as e:
                        print(f"Error removing file {filepath}: {e}")

            # Determine mimetype
            mimetype = 'application/zip' if filepath.endswith('.zip') else 'application/octet-stream'
            import mimetypes
            guess_type, _ = mimetypes.guess_type(filepath)
            if guess_type:
                mimetype = guess_type

            response = Response(generate(), mimetype=mimetype)
            
            # Robust Unicode Filename Handling
            from urllib.parse import quote
            try:
                # Encode filename for generic ascii compatibility
                safe_filename = download_name.encode('ascii', 'ignore').decode('ascii')
                if not safe_filename: safe_filename = "download"
                
                # Use RFC 5987 syntax for full Unicode support
                # key="ascii_name"; key*=UTF-8''unicode_name
                response.headers.set('Content-Disposition', 'attachment', filename=safe_filename)
                response.headers['Content-Disposition'] += f"; filename*=UTF-8''{quote(download_name)}"
            except Exception as e:
                print(f"Header encoding error: {e}")
                # Fallback
                response.headers.set('Content-Disposition', 'attachment', filename="download")

            response.headers.set('Content-Length', str(os.path.getsize(filepath)))
            return response
            
    return "File not found or download not complete", 404

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
    # Attempt to cleanup old files
    cleanup_old_downloads()
    
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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True, use_reloader=False)