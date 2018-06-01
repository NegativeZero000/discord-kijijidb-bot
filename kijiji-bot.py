# Kijiji Bot
# Uses Python 3.6.5

# Discord specific imports
import discord
from discord.ext import commands
from discord.ext.commands import Bot
# Threading
import asyncio
import aiofiles
# Miscellaneous imports
import logging
import threading
import os
from pathlib import Path
import json
from pprint import pprint
import datetime
import re
import random
import queue
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from listing import Listing, Base


# Set up Discord logging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Configuration file name. To be located in same directory as script
config_file_name = "bot_cfg.json"
default_command_prefix = "#"

class SearchConfig(object):
    '''Coordinates the pulling of listings from the database and posting them'''

    def __init__(self, dictionary):
        self.id = dictionary['id']
        self.search_indecies = dictionary['searchindecies']
        self.posting_channel = dictionary['channel']

    def __str__(self):
        return 'Id: {}\nSearch Indecies: {}\nChannel: {}\n'.format(
            self.id, self.searchindecies, self.posting_channel
        )

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
            title=self.title, description=self.description, color=discord.Colour(random.randint(0, 16777215)),
            url=self.url)
        listing_embed.add_field(name='Location', value=self.location, inline=True)
        listing_embed.add_field(name='Price', value=self.price, inline=True)
        listing_embed.set_image(url=self.imageurl)
        listing_embed.set_thumbnail(
            url=self.thumbnail)
        listing_embed.set_footer(text='Listed: {}'.format(self.posted))
        return listing_embed

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
    # Load the files key value pairs
    with open(config_file_path) as json_file:
        config_options = json.load(json_file)

    pprint(config_options)
else:
    print("The configuration file {} does not exist".format(config_file_path))

# Set the command prefix from config if possible
if "command_prefix" in config_options.keys():
    defined_command_prefix = config_options["command_prefix"]
    print("Using {} as a command declaration string".format(
        config_options["command_prefix"]))
else:
    print("Does not appear to be a key called 'command_prefix'. \
        Using default: {}".format(default_command_prefix))
    defined_command_prefix = default_command_prefix

bot = Bot(command_prefix=defined_command_prefix)

# Collect individual database search configs
search_configs = []
for search_config in config_options['search']:
    search_configs.append(SearchConfig(dictionary=search_config))
    print(search_config)

@bot.event
async def on_ready():
    """Event for when the bot is ready to start working"""
    print("Ready when you are")
    print("I am running on " + bot.user.name)
    print("With the id " + bot.user.id)
    await bot.change_presence(game=discord.Game(name='hard to get'))

@bot.command(pass_context=True)
async def ping(context, *args):
    """Verifcation that the bot is running and working."""
    await bot.say(":eight_spoked_asterisk: I'm here {}".format(
        context.message.author))
    # Remove the message that triggered this command
    await bot.delete_message(context.message)
    print("{} has pinged".format(context.message.author))

# # Initialize the bot with the config token
if "token" in (config_options.keys()):
    # Run the bot with the supplied token
    print('Discord.py version:', discord.__version__)

    print(config_options['search'])

    # bot.run(config_options["token"])

else:
    print("Does not appear to be a key called 'token'")
