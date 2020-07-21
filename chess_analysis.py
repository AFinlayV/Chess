# write a program to analyse my chess games
import pandas as pd
import chess.pgn
from stockfish import Stockfish as sf
import lichess.api
from lichess.format import SINGLE_PGN

USERNAME = 'AlexTheFifth'
FILENAME = 'lichess_{}.pgn'.format(USERNAME)
VERBOSE = False

#load lichess data from lichess.org
def load_user_data(name):
    '''
    load user data
    '''
    print('Loading user data for {}...'.format(USERNAME))
    user = lichess.api.user(name)
    user_data = user
    return user_data


def save_game_data(file):
    '''
    Save game data
    '''
    loadnew = input('Download all games from lichess? (y/n)')
    if loadnew == 'y' or loadnew == 'Y':
        print('Loading game data for {}... (this might take a while)'.format(USERNAME))
        pgn = lichess.api.user_games(USERNAME, format=SINGLE_PGN)
        with open(FILENAME, 'w') as f:
            f.write(pgn)
        print('data saved as: {}'.format(FILENAME))
    else:
        print('New games not downloaded for user {}'.format(USERNAME))




def load_game_data(file):
    '''
    load game data from FILENAME and return pandas DataFrame object
    '''
    print('Reading data from {}'.format(FILENAME), end = '')
    pgn = open(file)
    result = {}
    i = 0
    while True:
        i += 1
        game = chess.pgn.read_game(pgn)
        if game is None:
            break

        headers = dict(game.headers)
        headers["Moves"] = game.board().variation_san(game.mainline_moves())

        result["Game{}".format(i)] = headers

    verbose('Raw Data', result)

    df = pd.DataFrame.from_dict(data = result).transpose()
    verbose('Formatted data', df)
    return df

def verbose(message, data):
    '''
    print data when in verbose mode
    '''
    if VERBOSE:
        delimiter = '\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'
        print(delimiter, message, delimiter, data)
    else:
        print('[Use verbose mode to see {}]'.format(message))

def run():
    load_user_data(USERNAME)
    save_game_data(FILENAME)
    game_data = load_game_data(FILENAME)

run()
