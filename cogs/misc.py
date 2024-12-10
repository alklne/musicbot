import discord, random
from discord.ext import commands, tasks

class misc(commands.Cog):
    def __init__(self, bot):
        self.bot : commands.Bot = bot
        self.errorDescriptions = {
            commands.CommandNotFound : 'Command not found!',
            commands.BadArgument : 'Bad argument!',
            commands.BotMissingPermissions : 'I am missing the necessary permisisons to do this action!',
            commands.BotMissingRole : "I am missing the role required to run this command!",
            commands.ChannelNotFound : "Channel not found!",
            commands.CommandOnCooldown : "Command on cooldown!",
            commands.DisabledCommand : "This command is disabled!",
            commands.GuildNotFound : "Guild not found!",
            commands.TooManyArguments : "You don't need any arguments vro!",
            commands.UserNotFound : "User not found!",
            commands.MissingRequiredArgument : "Missing argument."
        }

    @commands.Cog.listener()
    async def on_command_error(self, interaction : discord.Interaction, error : commands.CommandError):
        channel : discord.TextChannel = interaction.message.channel
        errorEmbed = discord.Embed(color = discord.Color.red(), title = "A error has occured!", description = "Unexpected error! Please check the console for more information.")
        
        for errorType in self.errorDescriptions:
            if isinstance(error, errorType):
                errorEmbed.description = self.errorDescriptions[errorType]

        print(error)
        await channel.send(embed = errorEmbed)

def setup(bot):
    return bot.add_cog(misc(bot=bot))