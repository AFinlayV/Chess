import pandas as pd
import chess.pgn
from stockfish import Stockfish as sf
import lichess.api
from lichess.format import SINGLE_PGN
import json

'''
This program takes the username from lichess.org and returns:

- user metadata
- a top ten list of that user's best and worst ECO opening codes for both white and black.

Ideas for future features:

- game analysis to figure out where user went wrong on an opening using pychess or stockfish
- make it faster?
- dislay openings from ECO codes
'''

# Define global variables
USERNAME = 'AlexTheFifth'
FILENAME = 'lichess_{}.pgn'.format(USERNAME)
VERBOSE = False
NUM_GAMES = 500
delimiter = '\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'

# data types and lists for columns
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

GAME_DATA = [
    'ECO',
    'Date',
    'White',
    'Black',
    'Result',
    'Moves'
    ]

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

col = [
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

def load_user_data(name):

    '''
    load user data for USERNAME
    Returns Series of data for USERNAME
    '''

    print('Loading user data for {}...'.format(USERNAME))
    user_raw = json.dumps(lichess.api.user(name))
    user_json = json.loads(user_raw)
    user = pd.json_normalize(user_json)
    verbose('User Data', user.iloc(0)[0][USER_DATA])
    return user


def save_game_data(file):

    '''
    Save game data to FILENAME
    '''

    loadnew = input('Download {} games from lichess? (y/n) '.format(NUM_GAMES))
    if loadnew == 'y' or loadnew == 'Y':
        print('Loading {} games for {}... (this might take a while)'.format(NUM_GAMES, USERNAME))
        pgn = lichess.api.user_games(USERNAME, max = NUM_GAMES, format=SINGLE_PGN)
        with open(FILENAME, 'w') as f:
            f.write(pgn)
        print('data saved as: {}'.format(FILENAME))
    else:
        print('New games not downloaded for user {}'.format(USERNAME))




def load_game_data(file):

    '''
    load game data from FILENAME and return pandas DataFrame object

    Returns DataFrame
    '''

    print('Reading data from {}'.format(FILENAME))
    pgn = open(file)
    result = {}
    i = 0
    print('Creating DataFrame from file: {}'.format(FILENAME))
    # format PGN data as dict
    while True:
        i += 1
        game = chess.pgn.read_game(pgn)
        #verbose('Loading game number {}'.format(i), game)
        if game is None:
            break

        headers = dict(game.headers)
        headers["Moves"] = game.board().variation_san(game.mainline_moves())

        result["{}".format(i)] = headers

    verbose('Raw Data', result)
    df = pd.DataFrame.from_dict(data = result).transpose().astype(TYPE_DICT, errors = 'ignore')
    verbose('Formatted data', df)
    return df

def normalize(user, games):

    '''
    generate a list of lists with ECO, Result, and both usernames for each game
    generate a list of unique eco_lst

    Returns list of lists for game data (game_lst), list of ECO codes (eco_lst)

    '''

    game_lst = []
    eco_lst = []
    for game in games.iterrows():
        eco = game[1]['ECO']
        result = game[1]['Result']
        white_un = game[1]['White']
        black_un = game[1]['Black']

        game_lst.append([eco, result, white_un, black_un])
        if eco not in eco_lst:
            eco_lst.append(eco)

    return game_lst, eco_lst

def analyse(game_stats, eco_lst):
    '''
     generate a dataframe that contains:
     -count for each eco
     -W/L/D counts for each ECO for both black and WhiteElo
     - win percentages for each ECO as black and white

     Returns DataFrame

    '''

    # generate dataframe from normalized data index and columns

    df = pd.DataFrame(0, index = eco_lst, columns = col)

    #populate DataFrame
    for game in game_stats:
        eco = game[0]
        result = game[1]
        white = game[2]
        black = game[3]

        df.at[eco, 'eco_count'] += 1
        if white == USERNAME:
            if result == '1-0':
                df.at[eco, 'wins_white'] += 1
            elif result == '0-1':
                df.at[eco, 'loss_white'] += 1
            elif result == '1/2-1/2':
                df.at[eco, 'draws_white'] += 1
            else:
                print('error?')
        elif black == USERNAME:
            if result == '1-0':
                df.at[eco, 'loss_black'] += 1
            elif result == '0-1':
                df.at[eco, 'wins_black'] += 1
            elif result == '1/2-1/2':
                df.at[eco, 'draws_black'] += 1
            else:
                print('error?')
    # calculate win/loss percentages for each ECO code
    df['win_loss_white'] = (df['wins_white'] / (df['loss_white'] + df['wins_white'])) * 100
    df['win_loss_black'] = (df['wins_black'] / (df['loss_black'] + df['wins_black'])) * 100

    return df


def top_ten(df):
    '''
    display the top ten best and worst openings for USERNAME for both black and white

    '''
    pd.options.display.float_format = '{:.2f}%'.format
    print(delimiter,'Top 10 best games for white:', delimiter,
        df[df['eco_count'] > (NUM_GAMES * .01)].sort_values(by = 'win_loss_white', ascending = False)[['eco_count', 'win_loss_white']][0:10])
    print(delimiter,'Top 10 best games for black:', delimiter,
        df[df['eco_count'] > (NUM_GAMES * .01)].sort_values(by = 'win_loss_black', ascending = False)[['eco_count', 'win_loss_black']][0:10])
    print(delimiter,'Top 10 worst games for white:', delimiter,
        df[df['eco_count'] > (NUM_GAMES * .01)].sort_values(by = 'win_loss_white', ascending = True)[['eco_count', 'win_loss_white']][0:10])
    print(delimiter,'Top 10 worst games for black:', delimiter,
        df[df['eco_count'] > (NUM_GAMES * .01)].sort_values(by = 'win_loss_black', ascending = True)[['eco_count', 'win_loss_black']][0:10])

def verbose(message, data):
    '''
    print data when in verbose mode
    '''
    if VERBOSE:
        print(delimiter, message, delimiter, data)
    else:
        print('[{}]'.format(message))

def run():
    save_game_data(FILENAME)
    user = load_user_data(USERNAME)
    games = load_game_data(FILENAME)
    game_stats, eco_lst = normalize(user, games)
    df = analyse(game_stats, eco_lst)
    top_ten(df)

run()
