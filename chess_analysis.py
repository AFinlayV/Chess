# write a program to analyse my chess games
import pandas as pd
import chess.pgn
from stockfish import Stockfish as sf
import lichess.api
from lichess.format import SINGLE_PGN
import json

USERNAME = 'AlexTheFifth'
FILENAME = 'lichess_{}.pgn'.format(USERNAME)
VERBOSE = False
NUM_GAMES = 100


# data types
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

def load_user_data(name):
    '''
    load user data for USERNAME
    '''
    print('Loading user data for {}...'.format(USERNAME))
    user_raw = json.dumps(lichess.api.user(name))
    user_json = json.loads(user_raw)
    user = pd.json_normalize(user_json)
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
    '''
    print('Reading data from {}'.format(FILENAME))
    pgn = open(file)
    result = {}
    i = 0
    print('Creating DataFrame from file: {}'.format(FILENAME))
    while True:
        i += 1
        game = chess.pgn.read_game(pgn)
        verbose('Loading game number {}'.format(i), game)
        if game is None:
            break

        headers = dict(game.headers)
        headers["Moves"] = game.board().variation_san(game.mainline_moves())

        result["{}".format(i)] = headers

    verbose('Raw Data', result)
    df = pd.DataFrame.from_dict(data = result).transpose().astype(TYPE_DICT, errors = 'ignore')
    verbose('Formatted data', df)
    return df

def stats(user, games):
    '''
    display stats for USERNAME

    todo:
    *- count number of occorances of each ECO
    - calculate win or loss using USERNAME, White, Black, and Result
    - calculate W/L percentage for each ECO as white and black seperately
    -

    '''

    df = pd.DataFrame(columns = col)
    eco_count = {}
    #print(games)

    for game in games.iterrows():
        eco = game[1]['ECO']
        if eco not in eco_count:
            eco_count[eco] = 1
        elif eco in eco_count:
            eco_count[eco] = eco_count[eco] + 1
        else:
            print('error?')

    print(eco_count)

    print(user[USER_DATA])
    print(games[GAME_DATA])


def verbose(message, data):
    '''
    print data when in verbose mode
    '''
    delimiter = '\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'
    if VERBOSE:
        print(delimiter, message, delimiter, data)
    else:
        print('[{}]'.format(message))

def run():
    user = load_user_data(USERNAME)
    save_game_data(FILENAME)
    games = load_game_data(FILENAME)
    stats(user, games)

run()
