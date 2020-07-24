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
    print(user.iloc(0)[0])
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
    figure out a way to combine:

    the list of unique ECO codes (eco_lst)
    the list of game results (game_stats)

    to generate

    a dataframe with the following information on each row:
    {
    'ECO':'',
    'eco_count': 0,
    'wins_white': 0,
    'wins_black': 0,
    'loss_white': 0,
    'loss_black': 0,
    'draws_black': 0,
    'draws_white': 0,
    'win_loss_white': 0.0,
    'win_loss_black': 0.0
    }

    by (maybe) refactoring this code:


    # if white_un == USERNAME and result == '1-0':
    #     counts[eco]['wins_white'] = counts[eco]['wins_white'] + 1
    # elif white_un == USERNAME and result == '0-1':
    #     counts[eco]['loss_white'] = counts[eco]['loss_white'] + 1
    # elif white_un == USERNAME and result == '1/2-1/2':
    #     counts[eco]['draws_white'] = counts[eco]['draws_white'] + 1
    # elif black_un == USERNAME and result == '0-1':
    #     counts[eco]['wins_black'] = counts[eco]['wins_black'] + 1
    # elif black_un == USERNAME and result == '1-0':
    #     counts[eco]['loss_black'] = counts[eco]['loss_black'] + 1
    # elif black_un == USERNAME and result == '1/2-1/2':
    #     counts[eco]['draws_black'] = counts[eco]['draws_black'] + 1
    # else:
    #     print('error?')


    # try:
    #     counts[eco]['win_loss_white'] = counts[eco]['wins_white'] / counts[eco]['loss_white']
    #     counts[eco]['win_loss_black'] = counts[eco]['wins_black'] / counts[eco]['loss_black']
    # except:continue

    '''


    for game in game_stats:
        print(game)
    print(eco_lst)


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
    save_game_data(FILENAME)
    user = load_user_data(USERNAME)
    games = load_game_data(FILENAME)
    game_stats, eco_lst = normalize(user, games)
    analyse(game_stats, eco_lst)

run()
