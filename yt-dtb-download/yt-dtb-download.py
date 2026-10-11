# import yt_dlp

# url = "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"

# ydl_opts = {"outtmpl": "downloads/%(title)s.%(ext)s"}
# with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#     ydl.download([url])

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
url = "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"

# Step 3: Set options for yt-dlp
ydl_opts = {
    "outtmpl": f"{folder_name}/%(title)s.%(ext)s"  # Save in downloads folder with video title
}

# Step 4: Download the video
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])

print("Download complete!")
