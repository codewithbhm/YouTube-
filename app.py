from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)

# Ensure the downloads directory exists
os.makedirs("downloads", exist_ok=True)

# Serve the homepage
@app.route("/")
def index():
    return send_file("index.html")

# Helper function to configure yt_dlp options
def get_yt_dlp_options(filename_template, is_mp3=False, resolution=None):
    options = {
        "outtmpl": filename_template,
        "quiet": True,
    }

    # Attach cookies file if it exists
    if os.path.exists("cookies.txt"):
        options["cookiefile"] = "cookies.txt"

    if is_mp3:
        options["format"] = "bestaudio/best"
        options["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "320",
        }]
    else:
        options["format"] = f"bestvideo[height<={resolution}]+bestaudio/best"
        options["merge_output_format"] = "mp4"
        options["nooverwrites"] = True

    return options

# Route to download MP3
@app.route("/download_mp3", methods=["POST"])
def download_mp3():
    url = request.form.get("url")
    if not url:
        return jsonify({"error": "URL is required"})

    ydl_opts = get_yt_dlp_options("downloads/%(title)s.%(ext)s", is_mp3=True)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).rsplit(".", 1)[0] + ".mp3"
            return jsonify({"file_url": "/" + filename})
    except Exception as e:
        return jsonify({"error": str(e)})

# Route to download MP4
@app.route("/download_mp4", methods=["POST"])
def download_mp4():
    url = request.form.get("url")
    resolution = request.form.get("resolution")
    if not url or not resolution:
        return jsonify({"error": "URL and resolution are required"})

    ydl_opts = get_yt_dlp_options(
        f"downloads/%(title)s_{resolution}p.%(ext)s", resolution=resolution
    )

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = f'downloads/{info["title"]}_{resolution}p.mp4'
            return jsonify({"file_url": "/" + filename})
    except Exception as e:
        return jsonify({"error": str(e)})

# Route to serve downloaded files
@app.route("/downloads/<path:filename>")
def download_file(filename):
    return send_from_directory("downloads", filename, as_attachment=True)

# Start the Flask app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
