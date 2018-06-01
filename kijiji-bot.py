# Kijiji Bot
# Uses Python 3.6.5

# Discord specific imports
import discord
from discord.ext import commands
from discord.ext.commands import Bot
# Miscellaneous imports
import logging
import os
from pathlib import Path
from random import randint
# Database
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
# Custom Class
from listing import Listing, Base
from botconfig import BotConfig


# Set up Discord logging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Configuration file name. To be located in same directory as script
config_file_name = "bot_cfg.json"

class KijijiListing(object):
    '''The basic Kijiji Listing information'''

    def __init__(self, dictionary):
        self.url = dictionary['absoluteurl']
        self.imageurl = dictionary['imageurl']
        self.id = dictionary['id']
        self.posted = dictionary['postedasdate']
        self.title = dictionary['title']
        self.description = dictionary['shortdescription']
        self.location = dictionary['location']
        self.price = dictionary['price']
        self.thumbnail = 'https://www.shareicon.net/data/128x128/2016/08/18/810389_strategy_512x512.png'

    def __str__(self):
        return 'Title: {}\nDescription: {}\nPrice: {}\nURL: {}'.format(
            self.title, self.description, self.price, self.url
        )

    def to_embed(self):
        '''Created a discord embed from this instances properties'''
        listing_embed = discord.Embed(
            title=self.title, description=self.description, color=discord.Colour(randint(0, 16777215)),
            url=self.url)
        listing_embed.add_field(name='Location', value=self.location, inline=True)
        listing_embed.add_field(name='Price', value=self.price, inline=True)
        listing_embed.set_image(url=self.imageurl)
        listing_embed.set_thumbnail(
            url=self.thumbnail)
        listing_embed.set_footer(text='Listed: {}'.format(self.posted))
        return listing_embed

class DatabaseConnection(object):
    '''Governs the selecting and updating of listings from the database'''
    __slots__ = 'search_configs', 'connection_string', 'session'

    def __init__(self, search_configs, connection_string):
        self.search_configs = search_configs
        self.connection_string = connection_string

    def open(self):
        # Use the connection string to start a database session
        pass

    def close(self):
        # Close an existing session.
        pass


# Scripts running location. Only set if called via python.exe
__location__ = os.path.realpath(
    # From https://docs.python.org/3/library/os.path.html
    # If a component is an absolute path, all previous components
    # are thrown away and joining continues from the absolute path component.
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

# Load Configuration File
config_file_path = Path(os.path.join(__location__, config_file_name))

# Read in configuration file.
if(config_file_path.is_file()):
    print("Configuration found in: {}".format(config_file_path))

    # Initiate the bot config object from file
    bot_config = BotConfig(config_file_path)
    print(str(bot_config))
else:
    print("The configuration file {} does not exist".format(config_file_path))

bot = Bot(command_prefix=bot_config.command_prefix)

engine = create_engine(bot_config.db_url)
session = Session(bind=engine)
Base.metadata.create_all(engine)

@bot.event
async def on_ready():
    '''Event for when the bot is ready to start working'''
    print("Ready when you are")
    print("I am running on " + bot.user.name)
    print("With the id " + bot.user.id)
    await bot.change_presence(game=discord.Game(name=bot_config.randompresence()))

@bot.command(pass_context=True)
async def ping(context, *args):
    '''Verifcation that the bot is running and working.'''
    await bot.say(":eight_spoked_asterisk: I'm here {}".format(
        context.message.author))
    # Remove the message that triggered this command
    await bot.delete_message(context.message)
    print("{} has pinged".format(context.message.author))

@bot.command()
async def shutdown():
    '''Command to shut the bot down'''
    await bot.logout()

@bot.command(aliases=['np'])
async def newpresence():
    '''Change the bot presence to another from from config'''

    # Check to see if we have multiple options to choose from
    if bot_config.presence.count > 1:
        # Same one could possibly show.
        await bot.change_presence(game=discord.Game(name=bot_config.randompresence()))
    else:
        await bot.say('I only have one presence.')

@bot.command(pass_context=True)
async def getlisting(context, id):
    '''Get a listing from the database matching the id passed'''
    try:
        single_listing = session.query(Listing).first()
    except NoResultFound as e:
        print(e)
        await bot.say("No listings available")
        # Deal with that as well

    if(single_listing):
        await bot.send_message(destination=bot_config.search[0].posting_channel, embed=single_listing.to_embed())

# Run the bot with the supplied token
print('Discord.py version:', discord.__version__)

bot.run(bot_config.token)
print(dir(bot))
bot.close()
