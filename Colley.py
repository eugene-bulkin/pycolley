import numpy as np
from numpy.linalg import inv
from scipy.special import binom

class ColleyError(Exception):
  pass

class Colley:
  def __init__(self, games):
    self.games = games
  def margin_scale(self, winning_score, losing_score):
    prob = 0
    for p in range(losing_score + 1):
      prob += float(2 ** (winning_score - p - 1)) / float(2 ** (2 * winning_score - 1)) * \
                binom(winning_score + p - 1, winning_score - 1)
    return 1 - prob
  def process(self, weight_fn=None, use_margin=False):
    '''Accepts a weight function which takes a note about the game
    (e.g. overtime) to determine how to weight a game (don't give as much weight
    to OT and similar games because they were much closer), and whether we are
    using margin of victory to weigh our rankings as well.'''
    if weight_fn is None:
      weight_fn = lambda notes: 1
    teams = reduce(lambda a, b: a | set([b[0], b[2]]), self.games, set())
    ids = dict(zip(teams, range(len(teams))))
    ids_to_team = {v: k for k, v in ids.items()}
    A = 2 * np.eye(len(teams))
    b = np.ones(shape=(len(teams), 1))
    for game in self.games:
      # Assumes that the format is TEAM1,SCORE1,TEAM2,SCORE2,NOTES
      tm1, sc1, tm2, sc2, notes = game
      sc1, sc2 = int(sc1), int(sc2)
      winner = tm1 if sc1 > sc2 else tm2
      loser = tm1 if sc1 < sc2 else tm2
      # margin of victory weight, default to 1
      mov_weight = 1
      if use_margin:
        # if we are using margin of victory, then calculate the weight
        win_sc, lose_sc = max(sc1, sc2), min(sc1, sc2)
        mov_weight = self.margin_scale(win_sc, lose_sc)
      winner_id, loser_id = ids[winner], ids[loser]
      A[winner_id][loser_id] -= 1 * mov_weight * weight_fn(notes)
      A[loser_id][winner_id] -= 1 * mov_weight* weight_fn(notes)
      A[winner_id][winner_id] += 1 * mov_weight * weight_fn(notes)
      A[loser_id][loser_id] += 1 * mov_weight * weight_fn(notes)
      b[winner_id][0] += 0.5 * mov_weight * weight_fn(notes)
      b[loser_id][0] -= 0.5 * mov_weight * weight_fn(notes)
    rank_pairs = zip(range(len(teams)), np.dot(inv(A), b).T[0])
    to_team = lambda pair: (ids_to_team[pair[0]], pair[1])
    return map(to_team, sorted(rank_pairs, key=lambda p: -p[1]))
