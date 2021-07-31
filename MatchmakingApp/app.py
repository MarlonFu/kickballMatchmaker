from flask import Flask, render_template, url_for
from flask import request

import numpy as np 
import pandas as pd
from sklearn.cluster import KMeans

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
        player_stats['Kn'] = [int(request.form.get('knowledge'))]
        player_stats['S'] = [int(request.form.get('speed'))]
        player_stats['T'] = [int(request.form.get('throwing'))]
        player_stats['C'] = [int(request.form.get('catching'))]
        player_stats['B/K'] = [int(request.form.get('batting'))]

        player_stats_df = pd.DataFrame.from_dict(player_stats)

        player_data.table = player_data.table.append(player_stats_df)
        #print(player_stats_df)
        return render_template('home.html', table=player_data.table.to_html(index=False))


@app.route('/create_teams', methods=['GET'])
def create_teams():
    if request.method =='GET':
        if player_data.table.shape[0] < 2:
            error = 'Must have at least 2 players.'
            return render_template('home.html', table=player_data.table.to_html(index=False), error=error)
        else:
            player_data.table['Overall'] = player_data.table['Kn'] + player_data.table['S'] + player_data.table['T'] + player_data.table['C'] + player_data.table['B/K']
            results = generate_teams(player_data.table)

            team1_tbl = results[0].drop(columns=['Player Type'])
            team2_tbl = results[1].drop(columns=['Player Type'])
            
            team1_total = np.sum(team1_tbl['Overall'])
            team1_avg = np.mean(team1_tbl['Overall'])

            team2_total = np.sum(team2_tbl['Overall'])
            team2_avg = np.mean(team2_tbl['Overall'])

            team1_info = {'total': team1_total, 'avg': team1_avg}
            team2_info = {'total': team2_total, 'avg': team2_avg}
            return render_template('results.html', team1=team1_tbl.to_html(index=False), team2=team2_tbl.to_html(index=False), team1_info=team1_info, team2_info=team2_info)


def generate_teams(data):
    greedy_results = greedy_algorithm(data)
    kmeans_results = generate_clustered_teams(data)

    greedy_diff = np.absolute(np.sum(greedy_results[0]['Overall']) - np.sum(greedy_results[1]['Overall']))
    kmeans_diff = np.absolute(np.sum(kmeans_results[0]['Overall']) - np.sum(kmeans_results[1]['Overall']))

    if greedy_diff > kmeans_diff:
        print('k')
        return kmeans_results
    elif greedy_diff < kmeans_diff:
        print('g')
        return greedy_results
    elif greedy_diff == kmeans_diff:
        greedy_score = np.sum(np.absolute(generate_comparison_table(greedy_results[0], greedy_results[1]).drop(columns=['overall_total', 'overall_avg']).loc['Difference']))
        kmeans_score = np.sum(np.absolute(generate_comparison_table(kmeans_results[0], kmeans_results[1]).drop(columns=['overall_total', 'overall_avg']).loc['Difference']))
        
        if greedy_score < kmeans_score:
            print('g')
            return greedy_results
        else:
            print('k')
            return kmeans_results


def generate_clustered_teams(data):
    num_clusters = int(len(data.index) / 2)
    data = generate_clusters(data, num_clusters)

    kmeans_team_1 = pd.DataFrame(columns=data.columns)
    kmeans_team_2 = pd.DataFrame(columns=data.columns)

    kmeans_team_1_total_score = 0
    kmeans_team_2_total_score = 0
    
    

    for i in range(len(data.index)):
        player_type = data.iloc[i]['Player Type']
        if kmeans_team_1[kmeans_team_1['Player Type'] == player_type].shape[0] > kmeans_team_2[kmeans_team_2['Player Type'] == player_type].shape[0]:
            kmeans_team_2 = kmeans_team_2.append(data.iloc[i])
            kmeans_team_2_total_score += data.iloc[i]['Overall']
        elif kmeans_team_1[kmeans_team_1['Player Type'] == player_type].shape[0] < kmeans_team_2[kmeans_team_2['Player Type'] == player_type].shape[0]:
            kmeans_team_1 = kmeans_team_1.append(data.iloc[i])
            kmeans_team_1_total_score += data.iloc[i]['Overall']
        else:
            if kmeans_team_1_total_score > kmeans_team_2_total_score:
                kmeans_team_2 = kmeans_team_2.append(data.iloc[i])
                kmeans_team_2_total_score += data.iloc[i]['Overall']

            elif kmeans_team_1_total_score < kmeans_team_2_total_score:
                kmeans_team_1 = kmeans_team_1.append(data.iloc[i])
                kmeans_team_1_total_score += data.iloc[i]['Overall']

            else:
                indicator = np.random.randint(2)
                if indicator == 0:
                    kmeans_team_2 = kmeans_team_2.append(data.iloc[i])
                    kmeans_team_2_total_score += data.iloc[i]['Overall']
                elif indicator == 1: 
                    kmeans_team_1 = kmeans_team_1.append(data.iloc[i])
                    kmeans_team_1_total_score += data.iloc[i]['Overall']

    kmeans_team_1 = kmeans_team_1.sort_values('Overall', ascending=False).reset_index(drop=True)
    kmeans_team_2 = kmeans_team_2.sort_values('Overall', ascending=False).reset_index(drop=True)
    
    return [kmeans_team_1, kmeans_team_2]



def generate_clusters(data, num_clusters):
    kmeans = KMeans(n_clusters=num_clusters)
    y = kmeans.fit_predict(data.drop(columns=['Name', 'Overall']))
    data['Player Type'] = y
    return data.sort_values('Overall', ascending=False).reset_index(drop=True)



def greedy_algorithm(data):
    data = data.sort_values('Overall', ascending=False).reset_index(drop=True)

    team_1 = pd.DataFrame(columns=data.columns)
    team_2 = pd.DataFrame(columns=data.columns)

    team_1_total_score = 0
    team_2_total_score = 0


    for i in range(len(data.index)):
        if team_1_total_score > team_2_total_score:
            team_2 = team_2.append(data.iloc[i])
            team_2_total_score += data.iloc[i]['Overall']
        elif team_1_total_score < team_2_total_score:
            team_1 = team_1.append(data.iloc[i])
            team_1_total_score += data.iloc[i]['Overall']
        else:
            indicator = np.random.randint(2)
            if indicator == 0:
                team_1 = team_1.append(data.iloc[i])
                team_1_total_score += data.iloc[i]['Overall']
            else: 
                team_2 = team_2.append(data.iloc[i])
                team_2_total_score += data.iloc[i]['Overall']
    
    return [team_1, team_2]



def generate_comparison_table(team_1, team_2):
    teams = ['Team 1', 'Team 2']
    knowledge_total = [np.sum(team_1['Kn']), np.sum(team_2['Kn'])]
    running_total = [np.sum(team_1['S']), np.sum(team_2['S'])]
    throwing_total = [np.sum(team_1['T']), np.sum(team_2['T'])]
    catching_total = [np.sum(team_1['C']), np.sum(team_2['C'])]
    kicking_total = [np.sum(team_1['B/K']), np.sum(team_2['B/K'])]
    overall_total = [np.sum(team_1['Overall']), np.sum(team_2['Overall'])]
    overall_avg = [np.mean(team_1['Overall']), np.mean(team_2['Overall'])]
    metric_totals = pd.DataFrame(data={'team': teams, 'knowledge_total': knowledge_total, 'running_total': running_total,
                                        'throwing_total': throwing_total, 'catching_total': catching_total, 'kicking_total': kicking_total,
                                        'overall_total': overall_total, 'overall_avg': overall_avg})

    
    metric_totals = metric_totals.set_index('team')

    difference = metric_totals.loc['Team 1'] - metric_totals.loc['Team 2']
    difference.name = 'Difference'
    
    metric_totals = metric_totals.append(difference)

    percent_difference = (metric_totals.loc['Difference'] * 100 / metric_totals.loc['Team 1']).astype(int)#.astype(str) + '%'
    percent_difference.name = '% Difference'

    metric_totals = metric_totals.append(percent_difference)


    return metric_totals

if  __name__ == "__main__":
    app.run(debug=True)