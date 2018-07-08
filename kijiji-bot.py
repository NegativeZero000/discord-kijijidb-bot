# Kijiji Bot
# Uses Python 3.6.5

# Discord specific imports
import discord
from discord.ext import commands
from discord.ext.commands import Bot
# Miscellaneous imports
import asyncio
import logging
import os
from pathlib import Path
from random import randint
from datetime import datetime
# Database
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound
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
    bot_config = BotConfig.from_json_config(config_file_path)
    print(str(bot_config))
else:
    print("The configuration file {} does not exist".format(path=config_file_path))

# Initialize the bot
bot = Bot(command_prefix=bot_config.command_prefix)

# Prep SQLAlchemy
engine = create_engine(bot_config.db_url, pool_recycle=3600)
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

@bot.command(pass_context=True)
@commands.has_role('admin')
async def shutdown(context):
    '''Command to shut the bot down'''
    # Remove the message that triggered this command
    await bot.delete_message(context.message)
    await bot.logout()

@bot.command(pass_context=True)
async def status(context):
    ''' Reports pertinent bot statistics as an embed'''
    time_format = '%Y-%m-%d %H:%M:%S'

    status_embed = discord.Embed(
        title="Kijiji Bot Status",
        description="Quick snapshot of what is going on with the bot",
        color=discord.Colour(randint(0, 16777215))
    ).add_field(
        name='Last DB Check',
        value=bot_config.last_searched.strftime(time_format)
    ).add_field(
        name='Running Since',
        value=bot_config.when_started.strftime(time_format)
    )

    await bot.send_message(destination=context.message.channel, embed=status_embed)
    # Remove the message that triggered this command
    await bot.delete_message(context.message)

@bot.command(pass_context=True, aliases=['np'])
async def newpresence(context):
    '''Change the bot presence to another from from config'''

    # Get the current status of the bot so we can omit that from the choices.
    current_game = next(single_member.game.name
                        for single_member in bot.get_all_members()
                        if single_member.id == bot.user.id)

    # Check to see if we have multiple options to choose from
    if len(bot_config.presence) > 1:
        # Same one could possibly show.
        await bot.change_presence(game=discord.Game(name=bot_config.randompresence(current_game)))
    else:
        await bot.say('I only have one presence.')

    # Remove the message that triggered this command
    await bot.delete_message(context.message)

@bot.command(pass_context=True, aliases=['gl'])
async def getlisting(context, id):
    '''Get a listing from the database matching the id passed'''
    try:
        single_listing = session.query(Listing).filter(Listing.id == id).first()

        # print("channel:", bot_config.search[0].posting_channel.name, bot_config.search[0].posting_channel.id)
        await bot.send_message(destination=bot_config.search[0].posting_channel, embed=single_listing.to_embed())

        # Remove the message that triggered this command
        await bot.delete_message(context.message)
    except NoResultFound as e:
        print(e)
        await bot.say("No listings available")
        # Deal with that as wells

async def listing_watcher():
    ''' This is the looping task that will scan the database for new listings and post them to their appropriate channel'''
    await bot.wait_until_ready()

    while not bot.is_closed:
        # Process each search individually
        for single_search in bot_config.search:
            # Attempt to get new listings up to a certain number
            try:
                new_listings = session.query(Listing).filter(and_(Listing.new == 1, Listing.searchurlid.in_(single_search.search_indecies))).limit(bot_config.posting_limit)

                for new_listing in new_listings:
                    await bot.send_message(destination=single_search.posting_channel, embed=new_listing.to_embed())
                    # Flag the listing as old
                    new_listing.new = 0

                session.commit()
            except NoResultFound as e:
                await bot.say("No listings available")

            # Update the last search value in config. Used in status command
            bot_config.last_searched = datetime.now()

            # Breather between search configs
            await asyncio.sleep(1)

        # task runs every 60 seconds
        await asyncio.sleep(60)

# Run the bot with the supplied token
print('Discord.py version:', discord.__version__)

# Start the database monitoring task
bot.loop.create_task(listing_watcher())
bot.run(bot_config.token)
bot.close()
