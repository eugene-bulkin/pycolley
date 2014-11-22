from numpy import *

class ColleyError(Exception):
  pass

class Colley:
  def __init__(self, games, weights={None: 1, 'T': 0.5}):
    self.games = games
    # Process team names
    self.teams = []
    for t1, t2, gt in games:
      if t1 not in self.teams:
        self.teams.append(t1)
      if t2 not in self.teams:
        self.teams.append(t2)
    # We use None as a default for regulation wins/losses
    if None not in weights.keys():
      raise ColleyError('If you have custom weights, None must be a key in the denoting a regulation win.')
    self.weights = weights
    # This is used for displaying and updating records
    self.wrecords = None
    self.uwrecords = None
    self.record_weight = len(weights.keys()) * 2 - 1
    # In case of ties being allowed, they don't split into W/L
    if 'T' in weights.keys():
      self.record_weight -= 1
    # Memoize processing status
    self.wrankings = {}
    self.uwrankings = {}
    # True = weighted, False = unweighted
    self.processed = { True: False, False: False }
    print "Loaded data for Colley Matrix processing. %i games loaded." % len(games)

  def process(self, weighted=True):
    if self.processed[weighted]:
      print "Data already processed."
      return
    if len(self.games) is 0:
      print "No games to process."
      return
    print "Determining Colley Matrix rankings. Weighted: %s" % weighted
    # Preliminaries
    N = len(self.teams)
    # This is to ensure that we place the correct ratings with the correct team
    teams_sorted = sorted(self.teams)
    indices = dict(zip(teams_sorted, range(N)))
    teamindices = dict(zip(range(N),teams_sorted))
    # Default records
    if weighted:
      self.wrecords = dict(zip(teams_sorted, [[0 for j in range(self.record_weight + 1)] for i in range(N)]))
    else:
      self.uwrecords = dict(zip(teams_sorted, [[0 for j in range(self.record_weight + 1)] for i in range(N)]))
    # Initial matrices
    C = 2 * identity(N)
    B = [0 for i in range(N)]
    # Actual processing
    print "Computing Colley matrices..."
    for winner, loser, game_type in self.games:
      wID = indices[winner]
      lID = indices[loser]
      try:
        if weighted:
          weight = self.weights[game_type]
        else:
          weight = 1
      except KeyError, e:
        raise ColleyError("Invalid game outcome. No weight found for the game type '%s'." % game_type)
      C[wID][lID] -= weight
      C[lID][wID] -= weight
      C[wID][wID] += weight
      C[lID][lID] += weight
      B[lID] += 0.5 * weight
      B[wID] -= 0.5 * weight
      # Update records
      if weighted:
        self.wrecords[winner][int(round((1 - weight) * self.record_weight))] += 1
        self.wrecords[loser][int(round((weight) * self.record_weight))] += 1
      else:
        self.uwrecords[winner][int(round((1 - weight) * self.record_weight))] += 1
        self.uwrecords[loser][int(round((weight) * self.record_weight))] += 1
    # Compute rankings
    print "Computing rankings..."
    C = matrix(C)
    B = 1 - matrix(B).T
    R = C.I * B
    ranks = R.T.tolist()[0]
    for team, ranking in zip(range(N), ranks):
      if weighted:
        self.wrankings[teamindices[team]] = ranking
      else:
        self.uwrankings[teamindices[team]] = ranking
    print "Done."
    self.processed[weighted] = True

  def __str__(self):
    either_proc = reduce(lambda a,b: a or b, self.processed.values())
    both_proc = reduce(lambda a,b: a and b, self.processed.values())
    if not either_proc:
      # Rankings must have been processed for either weighted or unweighted
      raise ColleyError('Data not yet processed.')
    # If there's no non-regulation win/loss, don't say "REG"
    say_reg = not reduce(lambda p, t: p and (t is None or t is 'T'), self.weights.keys(), None in self.weights.keys())
    default_type = 'REG' if say_reg else ''
    # Create header
    head_data = ["Name"]
    sorted_weights = sorted(self.weights.items(), key=lambda w: w[1], reverse=True)
    head_data.extend((gt or default_type) + 'W' for gt, w in sorted_weights if gt is not 'T')
    if 'T' in self.weights.keys(): head_data.append('T')
    head_data.extend((gt or default_type) + 'L' for gt, w in sorted_weights[::-1] if gt is not 'T')
    if self.processed[True]:
      head_data.append('Rating (Weighted)')
    if self.processed[False]:
      head_data.append('Rating (Unweighted)')
    header = "\t".join(head_data)
    # Start making list
    result = [header]
    # If both processed, then have both rankings, weighted first
    if both_proc:
      rankings = ((team, (self.wrankings[team], self.uwrankings[team])) for team in self.wrankings.keys())
      sort_key = lambda r: r[1][0]
    else:
      rankings = self.wrankings.items() if self.processed[True] else self.uwrankings.items()
      sort_key = lambda r: r[1]
    sorted_rankings = sorted(rankings, key=sort_key, reverse=True)
    for team_name, rating in sorted_rankings:
      line = [team_name]
      if self.processed[True]:
        line.extend(str(r) for r in self.wrecords[team_name])
      else:
        line.extend(str(r) for r in self.uwrecords[team_name])
      # If both weighted and unweighted are processed, rating is a tuple
      if both_proc:
        line.extend(str(r) for r in rating)
      else:
        line.append(str(rating))
      result.append("\t".join(line))
    return "\n".join(result)