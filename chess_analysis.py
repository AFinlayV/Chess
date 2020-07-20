# write a program to analyse my chess games
import pandas as pd
import chess.pgn
from stockfish import Stockfish as sf



#load lichess PGN

pgn = open('lichess_AlexTheFifth.pgn')

# make list of games
game_lst = []



# format games as dict
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

print(result)

# create pandas DataFrame

df = pd.DataFrame.from_dict(data = result)


print(df)
