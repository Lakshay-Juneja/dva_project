import pandas as pd
import os
from math import floor

# --- 1. ROBUST DATA LOADING ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "IPL.csv")

if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"IPL dataset not found at {CSV_PATH}")

df_raw = pd.read_csv(CSV_PATH, low_memory=False)
df_raw.columns = df_raw.columns.str.lower().str.strip()

# Numeric conversions for raw
num_cols = ['runs_batter', 'runs_extras', 'runs_total', 'season', 'year']
for col in num_cols:
    df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce')

# Global flags
df_raw['is_wicket'] = df_raw['wicket_kind'].notna().astype(int)
df_raw['is_six'] = (df_raw['runs_batter'] == 6).astype(int)
df_raw['is_four'] = (df_raw['runs_batter'] == 4).astype(int)

# Era Mapping
def era_map(s):
    if 2008 <= s <= 2012: return "2008-2012"
    elif 2013 <= s <= 2017: return "2013-2017"
    elif 2018 <= s <= 2022: return "2018-2022"
    else: return "2023-2025"
df_raw['era'] = df_raw['season'].apply(era_map)

# --- 2. PAGE 1: OVERVIEW METRICS ---
overview_matches = pd.DataFrame({"Metric": ["Total Matches"], "Value": [df_raw['match_id'].nunique()]})
overview_runs = pd.DataFrame({"Metric": ["Total Runs"], "Value": [df_raw['runs_total'].sum()]})
overview_teams = pd.DataFrame({"Metric": ["Total Teams"], "Value": [df_raw['batting_team'].nunique()]})
overview_boundaries = pd.DataFrame({"Metric": ["Fours", "Sixes"], "Value": [df_raw['is_four'].sum(), df_raw['is_six'].sum()]})
total_wickets_global = df_raw['is_wicket'].sum()
global_avg_rr = (df_raw['runs_total'].sum() / len(df_raw)) * 6
runs_trend = df_raw.groupby('season')['runs_total'].sum().reset_index(name='Total Runs').sort_values('season')

# --- 3. PAGE 2: ERA-WISE ANALYSIS ---
match_stats_era = df_raw.groupby(['era', 'match_id']).agg({
    'runs_total': 'sum',
    'is_wicket': 'sum'
}).reset_index()

era_avg_stats = match_stats_era.groupby('era').agg({
    'runs_total': 'mean',
    'is_wicket': 'mean'
}).rename(columns={'runs_total': 'avg_match_score', 'is_wicket': 'avg_match_wickets'}).reset_index()

# Keep compatibility with old names if needed, but we'll use era_avg_stats
era_avg_score = era_avg_stats[['era', 'avg_match_score']]
era_avg_wickets = era_avg_stats[['era', 'avg_match_wickets']]

balls_era = df_raw.groupby(['era', 'match_id']).size().reset_index(name='balls')
runs_era = df_raw.groupby(['era', 'match_id'])['runs_total'].sum().reset_index()
rr_merge = pd.merge(runs_era, balls_era, on=['era', 'match_id'])
rr_merge['run_rate'] = (rr_merge['runs_total'] / rr_merge['balls']) * 6
era_runrate = rr_merge.groupby('era')['run_rate'].mean().reset_index()
era_six_counts = df_raw.groupby('era')['is_six'].sum().reset_index()
era_wicket_counts = df_raw.groupby('era')['is_wicket'].sum().reset_index()

# --- 4. PAGE 3: TEAM PERFORMANCE ---
matches_team = df_raw.groupby(['season', 'batting_team'])['match_id'].nunique().reset_index(name='Matches Played')
runs_team = df_raw.groupby(['season', 'batting_team'])['runs_total'].sum().reset_index(name='Total Runs')
wickets_team = df_raw.groupby(['season', 'bowling_team'])['is_wicket'].sum().reset_index().rename(columns={'bowling_team': 'batting_team', 'is_wicket': 'Wickets Taken'})
team_season_summary = matches_team.merge(runs_team, on=['season', 'batting_team']).merge(wickets_team, on=['season', 'batting_team'], how='left').fillna(0)
team_season_summary.rename(columns={'batting_team': 'Team'}, inplace=True)

def get_best_worst_seasons(team_name):
    t_data = team_season_summary[team_season_summary['Team'] == team_name]
    if t_data.empty: return "N/A", "N/A"
    best = t_data.loc[t_data['Total Runs'].idxmax(), 'season']
    worst = t_data.loc[t_data['Total Runs'].idxmin(), 'season']
    return int(best), int(worst)

# --- 5. NEW: PLAYER ANALYSIS ---
# Batter Stats
batter_stats = df_raw.groupby('batter').agg({
    'runs_batter': 'sum',
    'match_id': 'nunique'
}).rename(columns={'runs_batter': 'Runs', 'match_id': 'Matches'}).reset_index()

batter_balls = df_raw.groupby('batter').size().reset_index(name='Balls')
batter_stats = batter_stats.merge(batter_balls, on='batter')
batter_stats['Strike Rate'] = (batter_stats['Runs'] / batter_stats['Balls']) * 100
top_10_batters = batter_stats.sort_values('Runs', ascending=False).head(10)

# Bowler Stats
bowler_stats = df_raw.groupby('bowler').agg({
    'is_wicket': 'sum',
    'match_id': 'nunique',
    'runs_total': 'sum'
}).rename(columns={'is_wicket': 'Wickets', 'match_id': 'Matches', 'runs_total': 'Runs Conceded'}).reset_index()

bowler_balls = df_raw.groupby('bowler').size().reset_index(name='Balls')
bowler_stats = bowler_stats.merge(bowler_balls, on='bowler')
bowler_stats['Economy'] = (bowler_stats['Runs Conceded'] / (bowler_stats['Balls'] / 6))
top_10_bowlers = bowler_stats.sort_values('Wickets', ascending=False).head(10)

# --- 6. NEW: VENUE ANALYSIS ---
venue_stats = df_raw.groupby('venue').agg({
    'runs_total': 'sum',
    'is_wicket': 'sum',
    'match_id': 'nunique'
}).rename(columns={'runs_total': 'Total Runs', 'is_wicket': 'Total Wickets', 'match_id': 'Matches'}).reset_index()

# Filter venues with at least 5 matches for cleaner visualization
venue_stats = venue_stats[venue_stats['Matches'] >= 5]
venue_stats['Avg Score'] = venue_stats['Total Runs'] / venue_stats['Matches']
venue_stats['Avg Wickets'] = venue_stats['Total Wickets'] / venue_stats['Matches']
top_venues = venue_stats.sort_values('Avg Score', ascending=False).head(10)
top_wicket_venues = venue_stats.sort_values('Avg Wickets', ascending=False).head(10)

# --- 7. NEW: SEASON ANALYSIS ---
season_summary = df_raw.groupby('season').agg({
    'runs_total': 'sum',
    'is_wicket': 'sum'
}).rename(columns={'runs_total': 'Runs', 'is_wicket': 'Wickets'}).reset_index()

# --- 8. MATCH SHOWCASE (REMAINS) ---
def get_match_showcase(m_id):
    m_data = df_raw[df_raw['match_id'] == m_id].copy()
    if m_data.empty: return None
    teams = m_data['batting_team'].unique()
    t1, t2 = teams[0], teams[1] if len(teams) > 1 else "Opposition"
    def calc_score(team):
        td = m_data[m_data['batting_team'] == team]
        return f"{td['runs_total'].sum()}/{td['is_wicket'].sum()} ({(td.shape[0]//6) + (td.shape[0]%6)/10})"
    return {'team1': t1, 'team2': t2, 'score1': calc_score(t1), 'score2': calc_score(t2),
            'twos': (m_data['runs_batter'] == 2).sum(), 'fours': (m_data['runs_batter'] == 4).sum(), 'sixes': (m_data['runs_batter'] == 6).sum()}

featured_match_data = get_match_showcase(1426306)
def get_player_stats(p_name):
    # Quick lookup for player selection
    b_data = batter_stats[batter_stats['batter'] == p_name]
    w_data = bowler_stats[bowler_stats['bowler'] == p_name]
    res = {}
    if not b_data.empty:
        res['runs'] = b_data['Runs'].iloc[0]
        res['sr'] = b_data['Strike Rate'].iloc[0]
    if not w_data.empty:
        res['wickets'] = w_data['Wickets'].iloc[0]
        res['econ'] = w_data['Economy'].iloc[0]
    return res
