from pytube import YouTube

url = "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"  # replace with your video
yt = YouTube(url)
stream = yt.streams.get_highest_resolution()
stream.download(output_path="downloads")  # saves in 'downloads' folder
print("Download complete!")
