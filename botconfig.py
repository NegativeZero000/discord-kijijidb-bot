from json import load
from random import choice
from datetime import datetime
from validators import url
from discord import Object

class SearchConfig(object):
    '''Coordinates the pulling of listings from the database and posting them'''
    __slots__ = 'id', 'search_indecies', 'posting_channel', 'thumbnail'

    def __init__(self, dictionary):

        if 'id' in dictionary.keys():
            self.id = dictionary['id']
        else:
            raise ValueError('Parameter "id" is required')

        if 'search_indecies' in dictionary.keys():
            self.search_indecies = [item for item in dictionary['search_indecies'] if isinstance(item, int)]

            # Verify that search contains at least one item
            if self.search_indecies.count == 0:
                raise ValueError('Parameter "search" contains no integers')
        else:
            raise ValueError('Parameter "search_indecies" is required')

        if 'posting_channel' in dictionary.keys():
            self.posting_channel = Object(id=dictionary['posting_channel'])
        else:
            raise ValueError('Parameter "posting_channel" is required')

        if 'thumbnail' in dictionary.keys():
            if url(dictionary['thumbnail']):
                self.thumbnail = dictionary['thumbnail']
            else:
                print(f"Thumbnail for {self.id} failed url validation")

    def __str__(self):
        return 'Id: {}\nSearch Indecies: {}\nPosting Channel: {}'.format(
            self.id,
            ", ".join([str(x) for x in self.search_indecies]),
            self.posting_channel
        )


class BotConfig(object):
    ''' Contains all import and running configuration used for the bot'''
    __slots__ = 'command_prefix', 'token', 'search', 'presence', 'db_url', 'posting_limit', 'last_searched', 'when_started'

    def __init__(self, *, token, db_url, search, command_prefix='#',
                 presence=['hard to get'], posting_limit=3):
        '''Set and scrub settings'''

        self.token = token
        self.posting_limit = posting_limit
        self.db_url = db_url

        self.search = []
        for search_config in search:
            self.search.append(SearchConfig(dictionary=search_config))

        self.command_prefix = command_prefix
        self.presence = presence

        # Use the current time as when the bot was initialized
        self.when_started = datetime.now()

    @classmethod
    def from_json_config(cls, path):
        '''Using the file path of the config file import and scrub settings'''

        with open(path) as json_file:
            config_options = load(json_file)
            return cls(**config_options)

    def randompresence(self, *args):
        # Get a random presence from list
        return choice([option for option in self.presence if option not in args])

    def __str__(self):
        return 'Command Prefix: {} \nSearch: {} \nToken: {} \nPresence: {}'.format(
            self.command_prefix,
            "\n".join(str(x) for x in self.search),
            self.token,
            self.presence
        )
