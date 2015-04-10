import sys
sys.path.insert(0, '../../')

from Colley import *

fn = sys.argv[1]
games = [l.split(",")[1:6] for l in open(fn, 'r').read().strip().split("\n")]

def weight_fn(notes):
  if notes == '':
    return 1
  if notes == 'OT':
    return 0.75
  if notes == 'SO':
    return 0.5

def print_rankings(ranks):
  print " # \tScore\tTeam"
  print "===\t=====\t" + "=" * 20
  for i in range(len(ranks)):
    team, score = ranks[i]
    print "%3d\t%0.3f\t%s" % (i + 1, score, team)

colley = Colley(games)
print "Without any additional weighting:"
print_rankings(colley.process())
print ""
print "Weighted by regulation/overtime/shootout"
print_rankings(colley.process(weight_fn=weight_fn))
print ""
print "Weighted by margin of victory"
print_rankings(colley.process(use_margin=True))
print ""
print "Weighted by regulation/overtime/shootout and margin of victory"
print_rankings(colley.process(weight_fn=weight_fn, use_margin=True))
