from json import load
from random import choice

class SearchConfig(object):
    '''Coordinates the pulling of listings from the database and posting them'''

    def __init__(self, dictionary):

        if 'id' in dictionary:
            self.id = dictionary['id']
        else:
            raise ValueError('Parameter "id" is required')

        if 'search_indecies' in dictionary:
            self.search_indecies = [item for item in dictionary['search_indecies'] if isinstance(item, int)]

            # Verify that search contains at least one item
            if self.search_indecies.count == 0:
                raise ValueError('Parameter "search" contains no integers')
        else:
            raise ValueError('Parameter "search_indecies" is required')

        if 'posting_channel' in dictionary:
            self.posting_channel = dictionary['posting_channel']
        else:
            raise ValueError('Parameter "posting_channel" is required')

    def __str__(self):
        return 'Id: {}\nSearch Indecies: {}\nPosting Channel: {}'.format(
            self.id,
            ", ".join([str(x) for x in self.search_indecies]),
            self.posting_channel
        )


class BotConfig(object):
    ''' Contains all import configuration used for the bot'''
    __slots__ = 'command_prefix', 'token', 'search', 'presence'

    def __init__(self, path):
        '''Using the file path of the config file import and scrub settings '''

        # Set bot defaults where applicable
        default_command_prefix = "#"
        default_presence = 'hard to get'

        # Load from file
        with open(path) as json_file:
            config_options = load(json_file)

        # Check for the required token property
        if 'token' in config_options.keys():
            self.token = config_options['token']
        else:
            raise ValueError('Parameter "token" is required.')

        # Check for the required search object property
        self.search = []
        if 'search' in config_options.keys():
            for search_config in config_options['search']:
                self.search.append(SearchConfig(dictionary=search_config))
        else:
            raise ValueError('At least one "search" is required.')

        # Set the command prefix from config if possible
        if "command_prefix" in config_options.keys():
            self.command_prefix = config_options["command_prefix"]
        else:
            self.command_prefix = default_command_prefix

        # Load presences if any. Append default just in case
        self.presence = []
        if 'presence' in config_options.keys():
            self.presence = config_options['presence']

        if self.presence.count == 0:
            self.presence.append(default_presence)

    def randompresence(self):
        # Get a random presence from list
        return choice(self.presence)

    def __str__(self):
        return 'Command Prefix: {} \nSearch: {} \nToken: {} \nPresence: {}'.format(
            self.command_prefix,
            "\n".join(str(x) for x in self.search),
            self.token,
            self.presence
        )
