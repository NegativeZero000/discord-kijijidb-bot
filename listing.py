from discord import Embed, Colour
from json import loads
from random import randint
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# https://auth0.com/blog/sqlalchemy-orm-tutorial-for-python-developers/
class SearchURL(Base):
    __tablename__ = 'searchurls'
    urlid = Column(Integer, primary_key=True)
    url = Column(String)
    inserted = Column(DateTime)

class Listing(Base):
    __tablename__ = 'listings'

    id = Column(Integer, primary_key=True)
    url = Column(String)
    price = Column(String)
    title = Column(String)
    distance = Column(String)
    location = Column(String)
    posted = Column(DateTime)
    shortdescription = Column(String)
    lastsearched = Column(DateTime)
    searchurlid = Column(Integer, ForeignKey('searchurls.urlid'))
    imageurl = Column(String)
    discovered = Column(Integer)
    new = Column(Boolean)
    changes = Column(String)
    searchurl = relationship('SearchURL')

    def changes_to_string(self):
        '''Take the json string changes and convert it to formatted string for reading in embed'''
        changes_markdown = ''
        if(self.changes):
            for change in loads(self.changes):
                changes_markdown += f'__{change["Property"]}:__ _{change["Findings"]}_\n'
        return changes_markdown

    def to_embed(self, **kwargs):
        '''Created a discord embed from this instances properties'''
        # If this listing has been discovered before then it is possible there are changes
        # that should be shown in the message as well.
        if(self.discovered > 0):
            listing_description = (
                f'{self.shortdescription}\n\n'
                f'This listing has been found {self.discovered} time(s) before.\n'
            )
            if self.changes:
                listing_description += (
                    f'The following differences from the previous listing were identified\n'
                    f'{self.changes_to_string()}'
                )
        else:
            listing_description = self.shortdescription

        listing_as_embed = Embed(
            title=self.title, description=listing_description, color=Colour(randint(0, 16777215)),
            url=self.url)
        listing_as_embed.add_field(name='Location', value=self.location, inline=True)
        listing_as_embed.add_field(name='Price', value=self.price, inline=True)
        listing_as_embed.set_image(url=self.imageurl)
        listing_as_embed.set_footer(text='Listed: {}'.format(self.posted))
        if 'thumbnail' in kwargs:
            listing_as_embed.set_thumbnail(url=kwargs.get('thumbnail'))

        return listing_as_embed
