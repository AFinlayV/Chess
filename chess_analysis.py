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
NUM_GAMES = 500
VERBOSE = False

ECO_FILENAME = 'eco.json'
DELIMITER = '\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'

# data types and lists
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

def load_user_data(name):

    '''
    load user data for USERNAME
    Returns Series of data for USERNAME
    '''

    print('Loading user data for {}...'.format(name))
    user_raw = json.dumps(lichess.api.user(name))
    user_json = json.loads(user_raw)
    user = pd.json_normalize(user_json)
    verbose('User Data', user.iloc(0)[0][USER_DATA])
    return user


def save_game_data(file, load_new, un, num):

    '''
    Save game data to FILENAME
    '''

    if load_new:
        print('Loading {} games for {}... (this might take a while)'.format(num, un))
        pgn = lichess.api.user_games(un, max = num, format=SINGLE_PGN)
        with open(file, 'w') as f:
            f.write(pgn)
        print('data saved as: {}'.format(file))
    else:
        print('New games not downloaded for user {}'.format(un))

def load_eco(eco_file):
    '''
    loads ECO Data from ECO_FILENAME
    returns json object with:
    -board position in FEN format
    -moves in PGN format

    '''

    fh = open(eco_file)
    eco = fh.read()
    eco_json = json.loads(eco)
    eco_df = pd.DataFrame(data = eco_json)
    return eco_df


def load_game_data(file):

    '''
    load game data from FILENAME and return pandas DataFrame object

    Returns DataFrame
    '''

    print('Reading data from {}'.format(file))
    pgn = open(file)
    result = {}
    i = 0
    print('Creating DataFrame from file: {}'.format(file))
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

def analyse(game_stats, eco_lst, un):
    '''
     generate a dataframe that contains:
     -count for each eco
     -W/L/D counts for each ECO for both black and WhiteElo
     - win percentages for each ECO as black and white

     Returns DataFrame

    '''

    # generate dataframe from normalized data index and columns

    df = pd.DataFrame(0, index = eco_lst, columns = COL)

    #populate DataFrame
    for game in game_stats:
        eco = game[0]
        result = game[1]
        white = game[2]
        black = game[3]

        df.at[eco, 'eco_count'] += 1
        if white == un:
            if result == '1-0':
                df.at[eco, 'wins_white'] += 1
            elif result == '0-1':
                df.at[eco, 'loss_white'] += 1
            elif result == '1/2-1/2':
                df.at[eco, 'draws_white'] += 1
            else:
                print('error?')
        elif black == un:
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


def top_ten(df, eco):
    '''
    display the top ten best openings for both black and white by win percentage

    '''
    pd.options.display.float_format = '{:.2f}%'.format
    print(DELIMITER,'Top 10 best games for white:', DELIMITER,
        df[df['eco_count'] > (NUM_GAMES * .01)].sort_values(by = 'win_loss_white', ascending = False)[['eco_count', 'win_loss_white']][0:10])
    print(DELIMITER,'Top 10 best games for black:', DELIMITER,
        df[df['eco_count'] > (NUM_GAMES * .01)].sort_values(by = 'win_loss_black', ascending = False)[['eco_count', 'win_loss_black']][0:10])

def bot_ten(df, eco):
    '''
    display the top ten worst openings for both black and white by win percentage

    '''
    pd.options.display.float_format = '{:.2f}%'.format
    print(DELIMITER,'Top 10 worst games for white:', DELIMITER,
        df[df['eco_count'] > (NUM_GAMES * .01)].sort_values(by = 'win_loss_white', ascending = True)[['eco_count', 'win_loss_white']][0:10])
    print(DELIMITER,'Top 10 worst games for black:', DELIMITER,
        df[df['eco_count'] > (NUM_GAMES * .01)].sort_values(by = 'win_loss_black', ascending = True)[['eco_count', 'win_loss_black']][0:10])

def verbose(message, data):
    '''
    print data when in verbose mode
    '''
    if VERBOSE:
        print(DELIMITER, message, DELIMITER, data)
    else:
        print('[{}]'.format(message))

def load_data():
    '''
    load data based on user input and return data to main function

    '''
    un, num, load_new = user_input()
    fn = 'lichess_{}.pgn'.format(un)
    eco_fn = ECO_FILENAME
    save_game_data(fn, load_new, un, num)
    user = load_user_data(un)
    games = load_game_data(fn)
    game_stats, eco_lst = normalize(user, games)
    eco = load_eco(eco_fn)
    df = analyse(game_stats, eco_lst, un)
    return un, num, fn, user, games, df, eco

def user_input():
    '''
     take user input for what data to load and weather or not to download new data

    '''
    un = input('LiChess.org username (Default is {}) >'.format(USERNAME))
    if not un:
        un = USERNAME
    num = input('Number of games to load (Default is {}) >'.format(NUM_GAMES))
    if not num:
        num = NUM_GAMES
    load = input('Download {} games from LiChess? This might take a while... (y/n) >'.format(num))
    if load == 'y' or load == 'Y':
        load_new = True
    else:
        load_new = False
    return un, num, load_new

def most_used(df):
    '''
    print a list of the most used ECO codes and counts for each

    '''
    print(DELIMITER, 'Most used openings:', DELIMITER,df.sort_values(by='eco_count', ascending=False)['eco_count'][0:10], '\n')
    print()

def disp_user(user):
    '''
    display user data
    # TODO:
    -add formatting
    '''
    print(user.T)

def disp_eco(eco_df):
    '''
    takes user input of ECO codes (A00-E99) and displays relevant data loaded from ECO_FILENAME
    # TODO:
    -use pychess to display board setups with move list below
    '''
    while True:
        eco_code = input('Input ECO code ("q" to quit)>')
        if eco_code == 'q' or eco_code == 'Q':
            break
        try:
            print(eco_df[eco_df['eco'] == eco_code])
        except:
            print('ECO code not found. Try again')

def sel_analysis(user, df, eco):
    '''
    loop for user to select analysis type.
    '''
    while True:
        ip = input('Select analysis: \n1 - Top ten openings by win % \n2 - Bottom 10 openings by win % \n3 - Most used openings \n4 - User info \n5 - display ECO board and moves \nq - quit \n>')
        if ip == 'q' or ip == 'Q':
            break
        else:
            try:
                ip = int(ip)
                if ip < 1 or ip > 5:
                    print('Enter a number 1-5, or "q" to quit')
                    continue
            except:
                print('Enter a number 1-5, or "q" to quit')
                continue
        if ip == 1:
            top_ten(df, eco)
        elif ip == 2:
            bot_ten(df, eco)
        elif ip == 3:
            most_used(df)
        elif ip == 4:
            disp_user(user)
        elif ip == 5:
            disp_eco(eco)
        else:
            break

def run():
    un, num, fn, user, games, df, eco = load_data()
    sel_analysis(user, df, eco)

run()
