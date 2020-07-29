import pandas as pd
import chess.pgn
import lichess.api
from lichess.format import SINGLE_PGN
import json

'''
This program takes the username from lichess.org and returns:

- user metadata
- a top ten list of that user's best and worst ECO opening codes for both white and black.
-list of openings for given ECO codes


# TODO:
- make into a class
    takes as input:
        Username (required)
        number of games to load (default - 500)
        download or load from local file (default - load from file)
        verbose (default - False)
    build eco.json into class?
    returns:
        object containing:
            data:
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
'''

# Define global variables
USERNAME = 'AlexTheFifth'
NUM_GAMES = 500
VERBOSE = False
DEBUG = False

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

def user_input():
    # Get input from user for what data to analyse
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
    data = load_data(un, num, load_new)
    return data

def analysis_input(data):
    '''
    loop for user to select analysis type.
    '''
    while True:
        ip = input('Select analysis: \n1 - Top ten openings by win % \n2 - Bottom 10 openings by win % \n3 - Most used openings \n4 - User info \n5 - look up ECO \nq - quit \n>')
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
            top_ten(data)
        elif ip == 2:
            bot_ten(data)
        elif ip == 3:
            most_used(data)
        elif ip == 4:
            disp_user(data)
        elif ip == 5:
            disp_eco(data)
        else:
            break

def load_data(un, num, load_new):
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
    fn = 'lichess_{}.pgn'.format(un)
    if load_new:
        print('Loading {} games for {}... (this might take a while)'.format(num, un))
        pgn = lichess.api.user_games(un, max = num, format=SINGLE_PGN)
        with open(fn, 'w') as f:
            f.write(pgn)
        debug('data saved as: {}'.format(fn))
    else:
        print('New games not downloaded for user {}'.format(un))

    # Load Data about all ECO opening codes into a DataFrame (eco_df)
    debug('Loading ECO Database from {}...'.format(ECO_FILENAME))
    fh = open(ECO_FILENAME)
    eco = fh.read()
    eco_json = json.loads(eco)
    eco_df = pd.DataFrame(data = eco_json)
    verbose('ECO Data loaded', eco_df)

    # Load user data
    debug('Loading user data for {}...'.format(un))
    user_raw = json.dumps(lichess.api.user(un))
    user_json = json.loads(user_raw)
    user = pd.json_normalize(user_json)
    verbose('User Data loaded', user.iloc(0)[0][USER_DATA].T)

    # load game data in PGN format
    debug('Reading data from {}'.format(fn))
    pgn = open(fn)

    # format PGN data as dict
    games = {}
    i = 0
    debug('Creating DataFrame from file: {}'.format(fn))
    while True:
        i += 1
        game = chess.pgn.read_game(pgn)
        #verbose('Loading game number {}'.format(i), game)
        if game is None:
            break

        headers = dict(game.headers)
        headers["Moves"] = game.board().variation_san(game.mainline_moves())

        games["{}".format(i)] = headers
    verbose('Raw Data loaded', games)

    # create Dataframe from dict
    debug('Formatting games data...')
    df_raw = pd.DataFrame.from_dict(data = games).transpose().astype(TYPE_DICT, errors = 'ignore')
    verbose('Formatted games data', df_raw)

    # count occurences of each ECO code and genertate a list of all eco codes
    debug('Counting games...')
    game_lst = []
    eco_lst = []
    for game in df_raw.iterrows():

        eco = game[1]['ECO']
        result = game[1]['Result']
        white_un = game[1]['White']
        black_un = game[1]['Black']

        game_lst.append([eco, result, white_un, black_un])
        if eco not in eco_lst:
            eco_lst.append(eco)
    verbose('Games counted', eco_lst)


    #populate DataFrame .df from game_lst
    df = pd.DataFrame(0, index = eco_lst, columns = COL)
    i=1
    for game in game_lst:
        eco = game[0]
        result = game[1]
        white = game[2]
        black = game[3]
        if VERBOSE:
            print('Game {} '.format(i), white, black, result, eco)

        # Increment ECO counts
        df.at[eco, 'eco_count'] += 1

        # Increment win count
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
        i+=1

    # calculate win/loss percentages for each ECO code
    df['win_loss_white'] = (df['wins_white'] / (df['loss_white'] + df['wins_white'])) * 100
    df['win_loss_black'] = (df['wins_black'] / (df['loss_black'] + df['wins_black'])) * 100

    verbose('Loaded {} games for {}'.format(num, un), df)

    return [user, games, df, eco_lst, eco_df]



def top_ten(data):
    '''
    display the top ten best openings for both black and white by win percentage

    '''
    df = data[2]
    pd.options.display.float_format = '{:.2f}%'.format
    print(DELIMITER,'Top 10 best games for white:', DELIMITER,
        df[df['eco_count'] > (NUM_GAMES * .01)].sort_values(by = 'win_loss_white', ascending = False)[['eco_count', 'win_loss_white']][0:10])
    print(DELIMITER,'Top 10 best games for black:', DELIMITER,
        df[df['eco_count'] > (NUM_GAMES * .01)].sort_values(by = 'win_loss_black', ascending = False)[['eco_count', 'win_loss_black']][0:10])

def bot_ten(data):
    '''
    display the top ten worst openings for both black and white by win percentage

    '''
    df = data[2]
    pd.options.display.float_format = '{:.2f}%'.format
    print(DELIMITER,'Top 10 worst games for white:', DELIMITER,
        df[df['eco_count'] > (NUM_GAMES * .01)].sort_values(by = 'win_loss_white', ascending = True)[['eco_count', 'win_loss_white']][0:10])
    print(DELIMITER,'Top 10 worst games for black:', DELIMITER,
        df[df['eco_count'] > (NUM_GAMES * .01)].sort_values(by = 'win_loss_black', ascending = True)[['eco_count', 'win_loss_black']][0:10])

def most_used(data):
    '''
    print a list of the most used ECO codes and counts for each

    '''
    df = data[2]
    print(DELIMITER, 'Most used openings:', DELIMITER)
    print(df.sort_values(by='eco_count', ascending=False)['eco_count'][0:10], '\n')

def disp_user(data):
    '''
    display user data
    # TODO:
    -add formatting
    '''
    user = data[0]
    print(user.T)

def disp_eco(data):
    '''
    takes user input of ECO codes (A00-E99) and displays relevant data loaded from ECO_FILENAME
    # TODO:
    -use pychess to display board setups with move list
    '''
    eco_df = data[4]
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
        print(message)


def verbose(message, data):
    '''
    print data when in verbose mode
    '''
    if VERBOSE:
        print(DELIMITER, message, DELIMITER, data)
    else:
        print('[{}]'.format(message))

def run():
    data = user_input()
    analysis_input(data)

run()
