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
    print('Loading user data...')
    user = lichess.api.user(name)
    user_data = user['perfs']
    print(user_data)


def save_game_data(file):
    '''
    load game data
    '''
    print('Loading game data... (this might take a while)')
    pgn = lichess.api.user_games(USERNAME, format=SINGLE_PGN)
    with open(FILENAME, 'w') as f:
        print('.', end = '')
        f.write(pgn)



def load_game_data():
    pgn = open(FILENAME)
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

    verbose(result)

    df = pd.DataFrame.from_dict(data = result).transpose()
    verbose(df)
    return df

def verbose(message, data):
    delimiter = '\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'
    print(delimiter, message, delimiter, data)

def main():
    load_user_data(USERNAME)
    save_game_data(FILENAME)
    game_data = load_game_data(FILENAME)
