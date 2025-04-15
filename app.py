from flask import Flask, request, jsonify, send_from_directory, send_file
import yt_dlp
import os

app = Flask(__name__)

# Ana səhifəni göstər
@app.route('/')
def index():
    return send_file('index.html')

# MP3 yükləmə route
@app.route('/download_mp3', methods=['POST'])
def download_mp3():
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'URL is required'})

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
            return jsonify({'file_url': '/' + filename})
    except Exception as e:
        return jsonify({'error': str(e)})

# MP4 yükləmə route
@app.route('/download_mp4', methods=['POST'])
def download_mp4():
    url = request.form.get('url')
    resolution = request.form.get('resolution')

    if not url or not resolution:
        return jsonify({'error': 'URL and resolution are required'})

    ydl_opts = {
        'format': f'bestvideo[height<={resolution}]+bestaudio/best',
        'outtmpl': f'downloads/%(title)s_{resolution}p.%(ext)s',
        'merge_output_format': 'mp4',
        'nooverwrites': True,
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = f'downloads/{info["title"]}_{resolution}p.mp4'
            return jsonify({'file_url': '/' + filename})
    except Exception as e:
        return jsonify({'error': str(e)})

# Faylın yüklənməsi üçün route
@app.route('/downloads/<path:filename>')
def download_file(filename):
    return send_from_directory('downloads', filename, as_attachment=True)

# Vercel üçün handler
os.makedirs('downloads', exist_ok=True)
handler = app
