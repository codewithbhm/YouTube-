from flask import Flask, render_template, request, jsonify, send_from_directory
import yt_dlp
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

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
            'preferredquality': '320',  # High quality MP3
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

@app.route('/download_mp4', methods=['POST'])
def download_mp4():
    url = request.form.get('url')
    resolution = request.form.get('resolution')

    if not url or not resolution:
        return jsonify({'error': 'URL and resolution are required'})

    ydl_opts = {
        'format': f'bestvideo[height<={resolution}]+bestaudio/best',
        'outtmpl': f'downloads/%(title)s_{resolution}p.%(ext)s',  # Dynamic file name based on resolution
        'merge_output_format': 'mp4',
        'nooverwrites': True,  # Prevent overwriting existing files
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = f'downloads/{info["title"]}_{resolution}p.mp4'
            return jsonify({'file_url': '/' + filename})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/downloads/<path:filename>')
def download_file(filename):
    return send_from_directory('downloads', filename, as_attachment=True)

if __name__ == '__main__':
    os.makedirs('downloads', exist_ok=True)
    app.run(debug=True)