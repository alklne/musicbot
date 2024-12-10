import discord, os, asyncio, base64, random
from pytubefix import *
from discord.ext import commands

class music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot            # this is the bot instance
        self.playing = False      # are we playing music right now
        self.voiceClient = ''     # voice client storage
        self.waitingToInstall = True   # variable for waiting for stuff to install
        self.youtubeInstance = ''   # the current youtube instance
        self.index = 0    # where are we in the queue
        self.playlistMode = False   # playlist mode
        self.shuffle = False    # shuffle mode (technically also 'loops', never ends)
        self.lastShuffleSong = 0   # last shuffle index
        self.looping = False    # are we looping
        self.queue = []   # list full of urls

    # invokes when song download is completed
    def downloadCompleted(self):
        print("Done")
        self.waitingToInstall = False
    
    # start function, runs the loop
    async def start(self, channel):
        # set variables
        self.index = 0
        self.playing = True
        self.looping = False

        while self.playing:
            # get the url from our queue
            theUrl = self.queue[self.index]
            
            # download the song
            self.waitingToInstall = True
            self.youtubeInstance = YouTube(theUrl, on_complete_callback = self.downloadCompleted())
            stream = self.youtubeInstance.streams.filter(only_audio=True).first()
            if stream == None:
                self.queue.pop(self.index)
                await channel.send(f":warning: I cannot find a stream for {theUrl.removeprefix("https://")}, it will be removed from the queue. :warning:")
                if len(self.queue) - 1 <= 0:
                    await channel.send(":x: Failsafe triggered, disconnecting. (no more songs, sorry for the inconvienience) :x:")
                    break
                else:
                    continue

            stream.download(filename = "music.mp3")
            while self.waitingToInstall: await asyncio.sleep(.1)
            # send a richtext saying the song has begun
            playingEmbed = discord.Embed(color = discord.Color.purple(), title = "Playing song!", description = f"Now playing {self.youtubeInstance.title}!")
            playingEmbed.set_image(url = self.youtubeInstance.thumbnail_url)
            await channel.send(embed = playingEmbed)

            # make a new ffmpeg instance and play the song, store the voice client
            ffmpegInstance = discord.FFmpegPCMAudio(source = "./music.mp3", executable = "./ffmpeg.exe")
            self.voiceClient.play(source = ffmpegInstance)

            # while playing/paused, check if the channel has more then 1 person and wait until the song is over
            while self.voiceClient.is_playing() or self.voiceClient.is_paused():
                if len(self.voiceClient.channel.members) <= 1 and self.voiceClient.is_connected():
                    await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "Where is everybody?", description = f"Nobody is in the voice call. I'm gone!"))
                    await self.voiceClient.disconnect()
                    break

                await asyncio.sleep(.1)

            # check if we're connected, !disconnect now just disconnects you
            if not self.voiceClient.is_connected():
                break

            if self.looping:
                continue

            # the song has ended, do we have shuffle enabled? if we do, shuffle numbers until we get a number which wasn't the last shuffle song
            if self.shuffle:
                if len(self.queue) > 1:
                    while self.index == self.lastShuffleSong:
                        self.index = random.randint(0, len(self.queue)-1)

                    self.lastShuffleSong = self.index
                else:
                    print("doesn't matter")
                    pass

                continue
            
            self.index += 1;
            if self.index >= len(self.queue):
                # playlist mode? go back to the first index
                if self.playlistMode:
                    self.index = 0
                # if we're not in playlist mode, disconnect
                else:
                    await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "No more songs!", description = f"No more songs in the queue... leaving!"))
                    break

        if self.voiceClient.is_connected():
            print("disconnecting")
            await self.voiceClient.disconnect()
        
        # reset variables
        self.queue = []
        self.index = 0
        self.youtubeInstance = ""
        self.playing = False
        self.looping = False
    
    # search function that uses youtube to look up songs
    @commands.command()
    async def search(self, interaction : discord.Interaction, *, query = "fortnite vbucks hack"):
        caller : discord.Member = interaction.message.author
        channel : discord.TextChannel = interaction.message.channel

        # we must be in the voice channel to run this command
        if not caller.voice:
            return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "You can't run this command.", description = "You must be in a voice channel to run this command."))

        if self.playlistMode and self.playing:
            return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "You can't run this command.", description = "You are running a playlist, you may cancel audio playback with !dc"))

        # make a query to youtube, get the videos
        videos = Search(query = query).videos
        responce = ''  # <-- selection

        # construct a embed and send it with the results we got
        searchEmbed = discord.Embed(color = discord.Color.purple(), title = "Search results!", description = "Pick your poison.")
        for index in range(1,6):
            youtubeObject = videos[index]
            searchEmbed.add_field(name = f"Type '{index}' to play this song.", value = youtubeObject.title, inline=True)
        await channel.send(embed = searchEmbed)
        
        # wait to see if we get a responce to our search query, if we don't, cancel the command
        try:
            responce = await self.bot.wait_for("message",check=lambda x: x.channel.id == interaction.channel.id and interaction.author.id == x.author.id and [1, 2, 3, 4, 5, 6].count(int(x.content)) != 0,timeout = 15,)
        except asyncio.TimeoutError:
            await channel.send("Out of time")
            return
        
        # this is our youtube instance
        youtube = videos[int(responce.content)]
        self.queue.append(youtube.watch_url)

        if self.playing and self.voiceClient != None or self.playlistMode:
            # the loop is already started so there is no need to start it again, return
            return await channel.send(embed = discord.Embed(color = discord.Color.green(), title = "Added song to queue!", description = "Your song has been added to the queue."))
        else:
            # attempt to connect to the vc and start the loop
            self.voiceClient : discord.VoiceClient = await caller.voice.channel.connect()
            await self.start(channel)
    
    # views the queue (indev)
    @commands.command()
    async def tracks(self, interaction : discord.Interaction):
        channel : discord.TextChannel = interaction.message.channel
        finishedEmbed = discord.Embed(color = discord.Color.purple(), title = "Queue!")

        if self.youtubeInstance:
            finishedEmbed.description = f"Currently playing {self.youtubeInstance.title} {self.youtubeInstance.watch_url}"
        else:
            finishedEmbed.description = "Nothing is playing right now!"

        if len(self.queue) >= 1:
            for songURL in self.queue:
                youtubeInstance = YouTube(songURL)
                if self.playing and self.youtubeInstance.watch_url == youtubeInstance.watch_url: continue
                finishedEmbed.add_field(name = youtubeInstance.title, value = youtubeInstance.watch_url)
        elif len(self.queue) > 8:
            finishedEmbed.add_field(name = "Error", value = "There are too many songs to display! (patch soon)")
        else:
            finishedEmbed.add_field(name = "There is nothing in the queue right now!", value = "Type !url https://youtube.com/watch?=example or !search test to add songs to the queue.")

        await channel.send(embed = finishedEmbed)
    
    # skips a song
    @commands.command()
    async def skip(self, interaction : discord.Interaction):
        channel : discord.TextChannel = interaction.message.channel
        caller : discord.Member = interaction.message.author

        # we must be playing music for this command to work
        if not self.playing or self.voiceClient == None:
            return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "Not playing anything", description = "I am not playing anything there is nothing to skip"))
        
        # we must be in the voice call to run this command
        if not caller.voice:
            return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "You can't run this command.", description = "You must be in a voice channel to run this command."))
        
        # stop the voice client which in term skips the song
        self.voiceClient.stop()
        return await channel.send(embed = discord.Embed(color = discord.Color.green(), title = "Skipped.", description = "Skipped the song!"))

    # forcefully disconnects and stops audio playback
    @commands.command()
    async def dc(self, interaction : discord.Interaction):
        channel : discord.TextChannel = interaction.message.channel
        caller : discord.Member = interaction.message.author
        
        # we must be playing music for this command to work
        if not self.playing or self.voiceClient == None:
            return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "Can't disconnect", description = "I am not in a discord channel"))
        
        # we must be in the voice call to run this command
        if not caller.voice:
            return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "You can't run this command.", description = "You must be in a voice channel to run this command."))

        if self.voiceClient: 
            await self.voiceClient.disconnect()
            await channel.send(embed = discord.Embed(color = discord.Color.green(), title = "Disconnected.", description = "I have left the voice call."))

    # import from youtube playlist
    @commands.command()
    async def importFromPlaylist(self, interaction : discord.Interaction, *, inputtedURL):
        caller : discord.Member = interaction.message.author
        channel : discord.TextChannel = interaction.message.channel

        # we need a url
        if not inputtedURL.startswith("https://"):
            errorEmbed = discord.Embed(color = discord.Color.red(), title = "Invalid URL", description = "Not a valid youtube url.")
            await channel.send(embed = errorEmbed)
            return
        
        # we must be in the voice channel to run this command
        if not caller.voice:
            return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "You can't run this command.", description = "You must be in a voice channel to run this command."))

        if self.playlistMode and self.playing:
            return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "You can't run this command.", description = "You are running a playlist, you may cancel audio playback with !dc"))

        # add songs to the queue (might error if the failsafe doesn't work)
        playlist = Playlist(inputtedURL)
        for ytInstance in playlist.videos:
            self.queue.append(ytInstance.watch_url)
        
        if self.playing and self.voiceClient != None or self.playlistMode:
            # the loop is already started so there is no need to start it again, return
            return await channel.send(embed = discord.Embed(color = discord.Color.green(), title = f"Added {len(playlist.videos)} songs to queue!", description = "Your songs has been added to the queue."))
        else:
            # attempt to connect to the vc and start the loop
            self.voiceClient : discord.VoiceClient = await caller.voice.channel.connect()
            await self.start(channel)

    # use a youtube url to get a song when the search function is stupid
    @commands.command()
    async def url(self, interaction : discord.Interaction, *, inputtedURL):
        caller : discord.Member = interaction.message.author
        channel : discord.TextChannel = interaction.message.channel

        # we need a url
        if not inputtedURL.startswith("https://"):
            errorEmbed = discord.Embed(color = discord.Color.red(), title = "Invalid URL", description = "Not a valid youtube url.")
            await channel.send(embed = errorEmbed)
            return
        
        # we must be in the voice channel to run this command
        if not caller.voice:
            return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "You can't run this command.", description = "You must be in a voice channel to run this command."))

        if self.playlistMode and self.playing:
            return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "You can't run this command.", description = "You are running a playlist, you may cancel audio playback with !dc"))

        # add song to the queue (might error if the failsafe doesn't work)
        self.queue.append(inputtedURL)
        
        if self.playing and self.voiceClient != None or self.playlistMode:
            # the loop is already started so there is no need to start it again, return
            return await channel.send(embed = discord.Embed(color = discord.Color.green(), title = "Added song to queue!", description = "Your song has been added to the queue."))
        else:
            # attempt to connect to the vc and start the loop
            self.voiceClient : discord.VoiceClient = await caller.voice.channel.connect()
            await self.start(channel)

    # pause the current track
    @commands.command()
    async def pause(self, interaction : discord.Interaction):
        channel : discord.TextChannel = interaction.message.channel
        caller : discord.Member = interaction.message.author

        # we must be in the voice channel to run this command
        if not caller.voice:
            return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "You can't run this command.", description = "You must be in a voice channel to run this command."))

        # if we're playing music we can then check if it's paused and resume or if it's not paused we can pause it
        if self.voiceClient != None and self.playing:
            if self.voiceClient.is_paused():
                self.voiceClient.resume()
                await channel.send(embed = discord.Embed(color = discord.Color.green(), title = "Resuming!", description = "Resuming the current track!"));
            else:
                self.voiceClient.pause()
                await channel.send(embed = discord.Embed(color = discord.Color.blue(), title = "Paused", description = "Paused the current track!"));
        else:
            return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "Nothing is being played.", description = "Nothing is being played right now."))

    # loops the current track
    @commands.command()
    async def loop(self, interaction : discord.Interaction):
        channel : discord.TextChannel = interaction.message.channel
        caller : discord.Member = interaction.message.author

        # we must be in the voice channel to run this command
        if not caller.voice:
            return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "You can't run this command.", description = "You must be in a voice channel to run this command."))
        
        # we need to be playing music for this command to work
        if not self.playing or self.voiceClient == None:
            return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "Nothing is being played.", description = "Nothing is being played right now."))
        else:
            self.looping = not self.looping
            if self.looping:
                await channel.send(embed = discord.Embed(color = discord.Color.green(), title = "Looped!", description = "Looping is now enabled on current track!"));
            else:
                await channel.send(embed = discord.Embed(color = discord.Color.green(), title = "Looping Disabled", description = "Looping is now disabled on current track!"));
    
    @commands.command()
    async def toggle(self, interaction : discord.Interaction, what : str, mode):
        channel : discord.TextChannel = interaction.message.channel
        caller : discord.Member = interaction.message.author

        # we must be in the voice channel to run this command
        if not caller.voice:
            return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "You can't run this command.", description = "You must be in a voice channel to run this command."))
        
        # must be a valid option
        if not mode in ['on', 'off']:
            return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "You can't run this command.", description = "Invalid option, select on/off"))

        # sets modes
        if what == "playlist":
            # can't set playlistmode if we're already playing music
            if self.playing:
                return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "You can't run this command.", description = "Can't toggle playlist mode whilest playing music"))
            self.playlistMode = mode == "on"
        elif what == "shuffle":
            self.shuffle = mode == "on"
        else:
            return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "Toggle doesn't exist!", description = f"Cannot find toggle {what}"))

        await channel.send(embed = discord.Embed(color = discord.Color.green(), title = "Success", description = f"{what} is now {mode}"))

    @commands.command()
    async def playlist(self, interaction : discord.Interaction, action, *, argument = "FN2HBYF8UJ9YGHJIM2FB81U29JGNIB18U9FC3VDSG"):
        channel : discord.TextChannel = interaction.message.channel
        caller : discord.Member = interaction.message.author

        # we must be in the voice channel to run this command
        if not caller.voice:
            return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "You can't run this command.", description = "You must be in a voice channel to run this command."))
        
        # we must have playlist mode enabled to use this command
        if not self.playlistMode:
            return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "You can't run this command.", description = "Playlist mode is not activated."))
        
        # can't do anything with playlists unless we're not playing
        if self.playing:
                return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "You can't run this command.", description = "You can't use this command while music is playing. Please run !dc."))
        
        # we're saving a playlist
        if action == 'save':
            if argument == "FN2HBYF8UJ9YGHJIM2FB81U29JGNIB18U9FC3VDSG": return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "Missing argument", description = "A argument is required to run this command"))

            # we can't save a empty queue
            if len(self.queue) <= 0:
                return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "You can't run this command.", description = "You cannot save nothing."))

            # string shinanigans and encoding
            encodedString = ""
            if len(self.queue) > 1:
                for songURL in self.queue:
                    encodedString = f"{encodedString}{songURL}|"
            else:
                encodedString = f"{encodedString}{self.queue[0]}"
            encodedString = base64.b64encode(encodedString.encode())

            if os.path.isfile(f"{os.getcwd()}/playlists/{argument}.txt") == True:
                await channel.send("There is already a existing playlist with this name, do you want to overwrite it? Type yes to confirm or wait to cancel.")
                try:
                    responce = await self.bot.wait_for("message",check=lambda x: x.channel.id == interaction.channel.id and interaction.author.id == x.author.id and x.content.lower() == "yes" != 0,timeout = 15,)
                except asyncio.TimeoutError:
                    await channel.send("Cancelled action.")
                    return

            # saving
            with open(f"{os.getcwd()}/playlists/{argument}.txt", "w+") as file:
                file.write(str(encodedString).removeprefix("b'").removesuffix("''"))
                file.close()

            # completion
            return await channel.send(embed = discord.Embed(color = discord.Color.purple(), title = "All done!", description = "Playlist saved."))
        
        # we're loading a playlist
        elif action == 'load':
            if argument == "FN2HBYF8UJ9YGHJIM2FB81U29JGNIB18U9FC3VDSG": return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "Missing argument", description = "A argument is required to run this command"))

            # song url storage
            songurls = []

            # does it exist?
            if os.path.isfile(f"{os.getcwd()}/playlists/{argument}.txt") == False:
                return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "Error", description = "Playlist doesn't exist!"))

            # if we have some stuff in the queue ask before loading
            if len(self.queue) >= 1:
                await channel.send("Are you sure you want to load a playlist? The queue will be wiped. Type yes to confirm or wait to cancel.")
                try:
                    responce = await self.bot.wait_for("message",check=lambda x: x.channel.id == interaction.channel.id and interaction.author.id == x.author.id and x.content.lower() == "yes" != 0,timeout = 15,)
                except asyncio.TimeoutError:
                    await channel.send("Cancelled action.")
                    return
                
            # decode base64 and retrieve a array of song urls from the playlist
            try:
                with open(f"{os.getcwd()}/playlists/{argument}.txt", "r+") as file:
                    content = file.read().encode()
                    content = str(base64.b64decode(content)).removeprefix("b'").removesuffix("|'")
                    if content.find("|") != -1:
                        songurls = content.split("|")
                    else:
                        songurls = [content]
                    file.close()
            except: return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "Malformed Playlist", description = "Playlist is malformed, can't get data"))
            
            # play
            self.queue = songurls
            return await channel.send(embed = discord.Embed(color = discord.Color.green(), title = "Loaded Playlist", description = f"Playlist {argument} loaded ({len(self.queue)} songs)"))

        # we're viewing a playlist
        elif action == 'view':
            if argument == "FN2HBYF8UJ9YGHJIM2FB81U29JGNIB18U9FC3VDSG": return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "Missing argument", description = "A argument is required to run this command"))

            # does it exist?
            if os.path.isfile(f"{os.getcwd()}/playlists/{argument}.txt") == False:
                return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "Error", description = "Playlist doesn't exist!"))

            songurls = []
            songs = ""

            # decode base64 and retrieve a array of song urls from the playlist
            try:
                with open(f"{os.getcwd()}/playlists/{argument}.txt", "r+") as file:
                    content = file.read().encode()
                    content = str(base64.b64decode(content)).removeprefix("b'").removesuffix("|'")
                    if content.find("|") != -1:
                        songurls = content.split("|")
                    else:
                        songurls = [content]
                    file.close()
            except: return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "Malformed Playlist", description = "Playlist is malformed, can't get data"))

            try:
                for songURL in songurls:
                    youtubeInstance = YouTube(songURL)
                    songs = f"{songs}{youtubeInstance.title}\n"
            except:
                return await channel.send("Youtube API error")

            await channel.send(songs)
            return
        
        # seek all available playlists
        elif action == "viewAll":
            build = ""
            for name in os.listdir(f"{os.getcwd()}/playlists"):
                build = f"{build}{name}, "
            await channel.send(f"{build}")
            return
        
        # start the playlist
        elif action == "start":
            if len(self.queue) > 0 and not self.playing:
                self.voiceClient : discord.VoiceClient = await caller.voice.channel.connect()
                await self.start(channel)
            else:
                return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "Empty Queue/Already Playing", description = "Please run !dc or add songs to the playlist with !search/!url or load one"))

        else:
            return await channel.send(embed = discord.Embed(color = discord.Color.red(), title = "Invalid 'action'", description = f"{action} is not a valid action. Valid actions: save, load, view, viewAll, start"))




def setup(bot):
    return bot.add_cog(music(bot=bot))