# DISCLAIMER
- No cooldowns/permissions intergrated YET.
- This bot will only work on Windows, I do not plan on adding Linux support any time soon.
- This bot is designed for one server only, it will not work on multiple servers.
- This bot has no intergration for Spotify, Soundcloud, whatever. It only works with Youtube and it will stay that way.
- I will only provide instruction on how to install the bot. You're on your own to figure out how it all works.

# FEATURES
- Playlist 'saving', 'loading' and 'shuffle' (like Spotify you can make entire playlists that the bot stores)
- Youtube intergration: Search, URLs and the ability to load entire Youtube playlists using pytubefix
- Pausing, looping, everything you expect

# INSTALLATION
This bot was originally made for my friend group, but I slowly started to develop it thurther, and now here we are.
I won't bore you with the details, so here is how to install the bot.

1. If you don't have Python already, or your version is below 3.8 (rough estimate), install the latest build at Python.org
2. Unzip the source and navigate to wherever you unzipped it, press the bar with the path and type cmd.exe
3. Use the requirements.txt file to install all of the modules you need, the command to do this is pip install -r requirements.txt (or if you didn't put python in your PATH, py -m pip install -r requirements.txt)
4. Go to ffmpeg.org/download.html and install the .exe version of ffmpeg, put it in the same directory as the main.py file.
5. Create a new file named '.env' in the same directory as the main.py file and paste the following inside of it:
```
TOKEN = "Put your BOT TOKEN in here, you're expected to know how to get this."
```
6. Open the main.py file and keep the window open! If you did everything correctly you should now be running your very own music bot.
