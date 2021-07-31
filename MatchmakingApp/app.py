from flask import Flask, render_template, url_for
from flask import request

import numpy as np 
import pandas as pd

app = Flask(__name__)

class Players:
    def __init__(self):
        self.table = pd.DataFrame(columns=['Name', 'Kn', 'S', 'T', 'C', 'B/K'])

player_data = Players()

@app.route('/')
def index():
    return render_template('home.html', table=player_data.table.to_html(index=False ))


@app.route('/add_player', methods=['POST'])
def add_player():
    if request.method == 'POST':
        player_stats = dict()
        player_stats['Name'] = [request.form['name']]
        player_stats['Kn'] = [request.form.get('knowledge')]
        player_stats['S'] = [request.form.get('speed')]
        player_stats['T'] = [request.form.get('throwing')]
        player_stats['C'] = [request.form.get('catching')]
        player_stats['B/K'] = [request.form.get('batting')]

        player_stats_df = pd.DataFrame.from_dict(player_stats)

        player_data.table = player_data.table.append(player_stats_df)
        #print(player_stats_df)
        return render_template('home.html', table=player_data.table.to_html(index=False))

if  __name__ == "__main__":
    app.run(debug=True)