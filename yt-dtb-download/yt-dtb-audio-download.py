import os
import yt_dlp

# Step 1: Create downloads folder if it doesn't exist
folder_name = "downloads"
if not os.path.exists(folder_name):
    os.makedirs(folder_name)
    print(f"Folder '{folder_name}' created successfully!")
else:
    print(f"Folder '{folder_name}' already exists.")

# Step 2: Define the video URL (replace with your own video link)
url = "https://www.youtube.com/watch?v=z_-XCN7YPnU&list=RDz_-XCN7YPnU&start_radio=1"

# Step 3: Set options for yt-dlp to download audio only
ydl_opts = {
    "format": "bestaudio/best",  # best available audio
    "outtmpl": f"{folder_name}/%(title)s.%(ext)s",  # save in downloads folder
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",       # convert to mp3
            "preferredquality": "320",     # set quality to 320 kbps
        }
    ],
}

# Step 4: Download the audio
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])

print("Audio download complete!")
