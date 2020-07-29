

'''
This program takes the username from lichess.org and returns:

- user metadata
- a top ten list of that user's best and worst ECO opening codes for both white and black.
- list of openings for given ECO codes


# TODO:
- make into a class
    inputs:
        username (required)
        local file name (Default 'lichess_{username}.pgn')
        number of games to load (default - 500)
        download or load from local file (default - ?)
        local file name
        verbose (default - False)
        debug (default - False)

    returns:
        object containing:
            attributes:
                user - user metadata
                games - pychess object of all games Data
                df - DataFrame with each game as a row
                eco_lst - list of all ECO codes present in df
                eco_df - DataFrame of ECO statistics
            methods:
                top_ten - 10 best ECO codes for black and white
                bot_ten - 10 best ECO codes for black and white
                most_used - most used ECO codes
                least_used - least used ECO codes
                disp_user - User metadata
                disp_eco - info about an ECO code
                ...

- build eco.json into this class? seperate class? library?

- make load_data() return dict instead of list,
- change reference from list to dict in analysis functions (top_ten, bot_ten, etc.)


'''
# Load libraries
import json
import pandas as pd
import chess.pgn
import lichess.api
from lichess.format import SINGLE_PGN

# Define global variables
USERNAME = 'AlexTheFifth'
NUM_GAMES = 500
VERBOSE = False
DEBUG = True
ECO_FILENAME = 'eco.json'
DELIMITER = '\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'


# List of user data to display in disp_user()
USER_DATA = [
    'username',
    'count.all',
    'count.win',
    'count.loss',
    'perfs.blitz.rating',
    'perfs.bullet.rating',
    'perfs.correspondence.rating',
    'perfs.classical.rating',
    'perfs.rapid.rating'
    ]

# Dict of data types for data pulled from PGN file
TYPE_DICT = {
    'Event'             : 'string',
    'Site'              : 'string',
    'Date'              : 'datetime64',
    'Round'             : 'string',
    'White'             : 'string',
    'Black'             : 'string',
    'Result'            : 'string',
    'BlackElo'          : 'int16',
    'BlackRatingDiff'   : 'int16',
    'ECO'               : 'category',
    'Termination'       : 'string',
    'TimeControl'       : 'string',
    'UTCDate'           : 'datetime64',
    'UTCTime'           : 'datetime64',
    'Variant'           : 'string',
    'WhiteElo'          : 'int16',
    'WhiteRatingDiff'   : 'int16',
    'Moves'             : 'string'
    }
# List of columns for DataFrame that counts ECOs, wins, and losses
COL = [
    'eco_count',
    'wins_white',
    'wins_black',
    'loss_white',
    'loss_black',
    'draws_black',
    'draws_white',
    'win_loss_white',
    'win_loss_black'
    ]


class Player:
    def __init__(self, un, num, load_new):
        self.un = un
        self.num = num
        self.load_new = load_new

    def load_data(self):
        '''
        load data from:
            -LiChess.org or local pgn file
            -local ECO_FILENAME

        save PGN data to file

        return list:
            [
            user - user metadata
            games - pychess object of all games Data
            df - DataFrame with each game as a row
            eco_lst - list of all ECO codes present in df
            eco_df - DataFrame of ECO statistics
            ]
        '''
        # load new data (or not)
        self.fn = 'lichess_{}.pgn'.format(self.un)
        if self.load_new:
            print('Loading {} games for {}... (this might take a while)'.format(self.num, self.un))
            self.pgn = lichess.api.user_games(self.un, max = self.num, format=SINGLE_PGN)
            with open(self.fn, 'w') as f:
                f.write(self.pgn)
            debug('data saved as: {}'.format(self.fn))
        else:
            print('New games not downloaded for user {}'.format(self.un))

        # Load Data about all ECO opening codes into a DataFrame (eco_df)
        debug('Loading ECO Database from {}...'.format(ECO_FILENAME))
        fh = open(ECO_FILENAME)
        eco = fh.read()
        eco_json = json.loads(eco)
        self.eco_df = pd.DataFrame(data = eco_json)
        verbose('ECO Data loaded', self.eco_df)

        # Load user data
        debug('Loading player data for {}...'.format(self.un))
        user_raw = json.dumps(lichess.api.user(self.un))
        user_json = json.loads(user_raw)
        self.user = pd.json_normalize(user_json)
        verbose('Player Data loaded for {}'.format(self.un), self.user.iloc(0)[0][USER_DATA].T)

        # load game data in PGN format
        debug('Reading data from {}...'.format(self.fn))
        pgn = open(self.fn)
        verbose('Data read from {}'.format(self.fn), pgn)

        # format PGN data as dict
        self.games = {}
        i = 0
        debug('Loading raw data from file: {}...'.format(self.fn))
        while True:
            i += 1
            game = chess.pgn.read_game(pgn)
            #verbose('Loading game number {}'.format(i), game)
            if game is None:
                break

            headers = dict(game.headers)
            headers["Moves"] = game.board().variation_san(game.mainline_moves())

            self.games["{}".format(i)] = headers
        verbose('Raw data loaded from file: {}'.format(self.fn), self.games)

        # create Dataframe from dict
        debug('Importing raw data to Pandas...')
        self.df_raw = pd.DataFrame.from_dict(data = self.games).transpose().astype(TYPE_DICT, errors = 'ignore')
        verbose('Pandas DataFrame created', self.df_raw)

        # count occurences of each ECO code and genertate a list of all eco codes
        debug('Counting games...')
        game_lst = []
        self.eco_lst = []
        for game in self.df_raw.iterrows():

            eco = game[1]['ECO']
            result = game[1]['Result']
            white_un = game[1]['White']
            black_un = game[1]['Black']

            game_lst.append([eco, result, white_un, black_un])
            if eco not in self.eco_lst:
                self.eco_lst.append(eco)
        verbose('Games counted', self.eco_lst)


        #populate DataFrame .df from game_lst
        self.df = pd.DataFrame(0, index = self.eco_lst, columns = COL)
        i=1
        for game in game_lst:
            eco = game[0]
            result = game[1]
            white = game[2]
            black = game[3]
            if VERBOSE:
                print('Game {} '.format(i), white, black, result, eco)

            # Increment ECO counts
            self.df.at[eco, 'eco_count'] += 1

            # Increment win count
            if white == self.un:
                if result == '1-0':
                    self.df.at[eco, 'wins_white'] += 1
                elif result == '0-1':
                    self.df.at[eco, 'loss_white'] += 1
                elif result == '1/2-1/2':
                    self.df.at[eco, 'draws_white'] += 1
                else:
                    print('error?')
            elif black == self.un:
                if result == '1-0':
                    self.df.at[eco, 'loss_black'] += 1
                elif result == '0-1':
                    self.df.at[eco, 'wins_black'] += 1
                elif result == '1/2-1/2':
                    self.df.at[eco, 'draws_black'] += 1
                else:
                    print('error?')
            i+=1

        # calculate win/loss percentages for each ECO code
        self.df['win_loss_white'] = (self.df['wins_white'] / (self.df['loss_white'] + self.df['wins_white'])) * 100
        self.df['win_loss_black'] = (self.df['wins_black'] / (self.df['loss_black'] + self.df['wins_black'])) * 100

        verbose('Loaded {} games for {}'.format(self.num, self.un), self.df)

        return [self.user, self.games, self.df, self.eco_lst, self.eco_df]



    def top_ten(self):
        '''
        display the top ten best openings for both black and white by win percentage

        '''
        df = self.df
        pd.options.display.float_format = '{:.2f}%'.format
        print(DELIMITER,'Top 10 best games for white:', DELIMITER,
            df[df['eco_count'] > (NUM_GAMES * .01)].sort_values(by = 'win_loss_white', ascending = False)[['eco_count', 'win_loss_white']][0:10])
        print(DELIMITER,'Top 10 best games for black:', DELIMITER,
            df[df['eco_count'] > (NUM_GAMES * .01)].sort_values(by = 'win_loss_black', ascending = False)[['eco_count', 'win_loss_black']][0:10])

    def bot_ten(self):
        '''
        display the top ten worst openings for both black and white by win percentage

        '''
        df = self.df
        pd.options.display.float_format = '{:.2f}%'.format
        print(DELIMITER,'Top 10 worst games for white:', DELIMITER,
            df[df['eco_count'] > (NUM_GAMES * .01)].sort_values(by = 'win_loss_white', ascending = True)[['eco_count', 'win_loss_white']][0:10])
        print(DELIMITER,'Top 10 worst games for black:', DELIMITER,
            df[df['eco_count'] > (NUM_GAMES * .01)].sort_values(by = 'win_loss_black', ascending = True)[['eco_count', 'win_loss_black']][0:10])

    def most_used(self):
        '''
        print a list of the most used ECO codes and counts for each

        '''
        df = self.df
        print(DELIMITER, 'Most used openings:', DELIMITER)
        print(df.sort_values(by='eco_count', ascending=False)['eco_count'][0:10], '\n')

    def disp_user(self):
        '''
        display user data
        # TODO:
        -add formatting
        '''
        user = self.user
        print(user.iloc(0)[0][USER_DATA].T)

    def disp_eco(self):
        '''
        takes user input of ECO codes (A00-E99) and displays relevant data loaded from ECO_FILENAME
        # TODO:
        -use pychess to display board setups with move list
        '''
        eco_df = self.eco_df
        while True:
            eco_code = input('Input ECO code ("q" to quit)>')
            if eco_code == 'q' or eco_code == 'Q':
                break
            else:
                try:
                    print(eco_df[eco_df['eco'] == eco_code])
                except:
                    print('ECO code not found. Try again')
                    continue

def debug(message):
    if DEBUG:
        print(DELIMITER, message, DELIMITER)


def verbose(message, data):
    '''
    print data when in verbose mode
    '''
    if VERBOSE:
        print(DELIMITER, message, DELIMITER, data)
    else:
        print('[{}]'.format(message))

def run():
    p1 = Player(USERNAME, NUM_GAMES, True)
    p1.load_data()
    p1.disp_user()
    p1.top_ten()
    p1.bot_ten()
    p1.most_used()



run()
