# Load libraries
import json
import pandas as pd
import chess.pgn
import lichess.api
from lichess.format import SINGLE_PGN

# Define global variables
USERNAME = 'AlexTheFifth'
NUM_GAMES = 1000
VERBOSE = False
DEBUG = False
ECO_FILENAME = 'eco.json'
DELIMITER = '\n<=>~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~<=>\n'


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
    '''
    attributes:
        .user
            user metadata
        .games
            pychess object of all games Data
        .df
            DataFrame with each game as a row
        .eco_lst
            list of all ECO codes present in df
        .eco_df
            DataFrame of ECO statistics

    methods:
        .disp_user()
            display user Data
        .most_used()
            most used openings
        .best(num, side)
            return the best {num} openings for {side}
        .worst(num, side)
            return the worst {num} openings for {side}
        .best_and_worst(num)
            return best and worst {num} for both black and white
    '''

    def __init__(self, un, num, load_new):
        '''
        load data from:
            -LiChess.org or local pgn file
            -local ECO_FILENAME

        save PGN data to file

        sets attributes
            .user - user metadata
            .games - pychess object of all games Data
            .df - DataFrame with each game as a row
            .eco_lst - list of all ECO codes present in df
            .eco_df - DataFrame of ECO statistics
        '''
        self.un = un
        self.num = num
        self.load_new = load_new

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

            # Increment win counts
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

    def best(self, num, side):
        df = self.df
        best = df[df['eco_count'] > (NUM_GAMES * .01)].sort_values(by = 'win_loss_{}'.format(side), ascending = False)[['eco_count', 'win_loss_{}'.format(side)]][0:num]
        return best

    def worst(self, num, side):
        df = self.df
        worst = df[df['eco_count'] > (NUM_GAMES * .01)].sort_values(by = 'win_loss_{}'.format(side), ascending = True)[['eco_count', 'win_loss_{}'.format(side)]][0:num]
        return worst

    def best_and_worst(self, num):
        print(DELIMITER, '{}\'s top {} for white'.format(self.un, num), DELIMITER, self.best(num, 'white'))
        print(DELIMITER, '{}\'s top {} for black'.format(self.un, num), DELIMITER, self.best(num, 'black'))
        print(DELIMITER, '{}\'s bottom {} for white'.format(self.un, num), DELIMITER, self.worst(num, 'white'))
        print(DELIMITER, '{}\'s bottom {} for black'.format(self.un, num), DELIMITER, self.worst(num, 'black'))

    def most_used(self, num):
        df = self.df
        print(DELIMITER, '{}\'s most used {} openings:'.format(self.un, num), DELIMITER)
        print(df.sort_values(by='eco_count', ascending=False)['eco_count'][0:num], '\n')

    def disp_user(self, data_lst):
        user = self.user.iloc(0)[0][data_lst].T
        print(DELIMITER, 'Player data for {}'.format(self.un), DELIMITER, user)



class Openings:
    '''
    attributes:
        .eco_df
            DataFrame of data from eco.json

    methods:
        .disp_eco(eco)
            display all instances of ECO value (A00-E99) in eco.json

    '''

    def __init__(self, fn):
        # Load Data about all ECO opening codes into a DataFrame (eco_df)
        self.fn = fn
        debug('Loading ECO Database from {}...'.format(self.fn))
        fh = open(self.fn)
        eco = fh.read()
        eco_json = json.loads(eco)
        self.eco_df = pd.DataFrame(data = eco_json)
        verbose('ECO Data loaded', self.eco_df)

    def disp_eco(self, eco):
        eco_df = self.eco_df
        eco_code = eco
        try:
            print(eco_df[eco_df['eco'] == eco_code])
        except:
            print('ECO code not found. Try again')


def debug(message):
    if DEBUG:
        print(DELIMITER, message, DELIMITER)

def verbose(message, data):
    if VERBOSE:
        print(DELIMITER, message, DELIMITER, data)
    else:
        print('[{}]'.format(message))

def run():
    p1 = Player(USERNAME, NUM_GAMES, False)
    p1.disp_user(USER_DATA)
    p1.best_and_worst(5)
    p1.most_used(10)

run()
