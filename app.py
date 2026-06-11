"""
Baseball Defensive Assignment Scheduler
========================================
Roster: P1–P13 (13 players)
Games:  14 games, 6 innings each
Field positions per inning: 9 (positions 1–9)
  1=Pitcher, 2=Catcher, 3=1B, 4=2B, 5=3B, 6=SS, 7=LF, 8=CF, 9=RF
 
Rules:
  - 13 players, 9 on field each inning → 4 players sit each inning
  - Players can play only one position per inning
  - Each player plays at most one extra inning compared to any teammate per game
    (with 13 players × 6 innings = 78 player-inning slots, 9 per inning,
     that gives each player roughly 4–5 innings per game: some get 4, some get 5)
  - Pitchers: P3,P4,P6,P9,P10,P12,P13 can pitch
      • Max 2 consecutive innings pitching
      • Once removed from pitching they cannot re-enter as pitcher
  - Catcher-eligible: P1, P4, P9, P12
  - Cannot play 3B (pos 5): P2, P5, P7
  - Equal playing time across 14 games balanced as tightly as possible
"""
 
import random
from copy import deepcopy
from collections import defaultdict
 
# ── constants ────────────────────────────────────────────────────────────────
NUM_PLAYERS  = 13
NUM_GAMES    = 14
NUM_INNINGS  = 6
FIELD_SIZE   = 9          # positions on field per inning
BENCH_SIZE   = NUM_PLAYERS - FIELD_SIZE  # 4 sit each inning
 
PLAYERS      = [f"P{i}" for i in range(1, NUM_PLAYERS + 1)]
 
PITCHER_POS  = 1
CATCHER_POS  = 2
THIRD_POS    = 5
 
PITCHER_ELIGIBLE  = {"P3","P4","P6","P9","P10","P12","P13"}
CATCHER_ELIGIBLE  = {"P1","P4","P9","P12"}
NO_THIRD_BASE     = {"P2","P5","P7"}
 
POSITION_NAMES = {
    1:"Pitcher", 2:"Catcher", 3:"1st Base", 4:"2nd Base",
    5:"3rd Base", 6:"Shortstop", 7:"Left Field",
    8:"Center Field", 9:"Right Field", 0:"Bench"
}
 
random.seed(42)   # reproducible output
 
# ── helpers ──────────────────────────────────────────────────────────────────
 
def can_play_position(player: str, pos: int) -> bool:
    """Return True if player is allowed to play the given position."""
    if pos == PITCHER_POS  and player not in PITCHER_ELIGIBLE:
        return False
    if pos == CATCHER_POS  and player not in CATCHER_ELIGIBLE:
        return False
    if pos == THIRD_POS    and player in NO_THIRD_BASE:
        return False
    return True
 
 
def schedule_game(game_number: int, season_innings: dict) -> dict:
    """
    Build a full 6-inning assignment for one game.
 
    Returns:
        assignments[inning][player] = position (0 = bench)
    """
    # ── inning-level playing-time balance ──────────────────────────────────
    # Total player-inning slots = 9 * 6 = 54
    # 54 / 13 ≈ 4.15  →  some play 4 innings, some play 5
    # We give each player a "target" innings count:
    #   - sort by season_innings ascending so those who played least go first
    #   - assign 5 innings to the 2 most-rested, 4 to the rest
    #     (actually 54 = 13*4 + 2, so exactly 2 players get 5)
    order = sorted(PLAYERS, key=lambda p: (season_innings[p], random.random()))
    target = {p: 4 for p in PLAYERS}
    for p in order[:2]:        # 2 players get an extra inning
        target[p] = 5
 
    # ── pitcher state machine ──────────────────────────────────────────────
    # pitcher_state[player] = {
    #   'active': bool,        currently pitching
    #   'done':   bool,        removed, cannot re-enter
    #   'consec': int,         consecutive innings pitched
    # }
    pitcher_state = {p: {'active': False, 'done': False, 'consec': 0}
                     for p in PLAYERS}
    current_pitcher = None
 
    # ── build inning-by-inning ─────────────────────────────────────────────
    assignments = {}          # assignments[inning] = {player: pos}
    innings_played = defaultdict(int)
 
    for inning in range(1, NUM_INNINGS + 1):
        # Players still needing innings
        remaining = {p: target[p] - innings_played[p] for p in PLAYERS}
        innings_left = NUM_INNINGS - inning + 1   # including current inning
 
        # Must-play: remaining target == innings left (can't afford to sit)
        must_play = {p for p, r in remaining.items() if r >= innings_left}
        # May play: have innings remaining
        may_play  = {p for p, r in remaining.items() if r > 0} - must_play
 
        # We need exactly 9 on field
        if len(must_play) > FIELD_SIZE:
            # Edge case: force some to bench (adjust targets down by 1)
            extras = list(must_play - set(order[:2]))
            random.shuffle(extras)
            for p in extras[:len(must_play)-FIELD_SIZE]:
                target[p] = max(0, target[p] - 1)
                must_play.discard(p)
                may_play.add(p)
 
        playing = set(must_play)
        needed = FIELD_SIZE - len(playing)
        pool = sorted(may_play, key=lambda p: (-remaining[p], random.random()))
        playing.update(pool[:needed])
        bench = set(PLAYERS) - playing
 
        # ── assign positions ───────────────────────────────────────────────
        inning_assign = {p: 0 for p in bench}   # 0 = bench
 
        # 1) Determine pitcher for this inning
        pitcher = _assign_pitcher(inning, playing, pitcher_state, current_pitcher)
        if pitcher:
            inning_assign[pitcher] = PITCHER_POS
            current_pitcher = pitcher
        unassigned = playing - {pitcher} if pitcher else set(playing)
 
        # 2) Assign catcher
        catcher_pool = [p for p in unassigned if p in CATCHER_ELIGIBLE]
        if not catcher_pool:
            raise RuntimeError(f"Game {game_number} inning {inning}: no catcher available!")
        catcher = random.choice(catcher_pool)
        inning_assign[catcher] = CATCHER_POS
        unassigned -= {catcher}
 
        # 3) Assign remaining 7 positions (3-9) respecting constraints
        field_positions = list(range(3, FIELD_SIZE + 1))  # 3..9
        random.shuffle(field_positions)
        unassigned_list = list(unassigned)
        random.shuffle(unassigned_list)
 
        assigned_positions = _assign_remaining(unassigned_list, field_positions)
        inning_assign.update(assigned_positions)
 
        assignments[inning] = inning_assign
        for p in playing:
            innings_played[p] += 1
 
        # update pitcher consecutive count
        for p in PLAYERS:
            ps = pitcher_state[p]
            if p == pitcher:
                ps['active'] = True
                ps['consec'] += 1
                if ps['consec'] >= 2:
                    # hit max consecutive; mark done after this inning
                    ps['done'] = True
                    ps['active'] = False
            else:
                if ps['active']:
                    # was pitching last inning, now removed
                    ps['done']   = True
                    ps['active'] = False
                ps['consec'] = 0
 
    return assignments
 
 
def _assign_pitcher(inning, playing, pitcher_state, current_pitcher):
    """Choose a pitcher for this inning respecting all pitching rules."""
    # Can the current pitcher continue?
    if current_pitcher and current_pitcher in playing:
        ps = pitcher_state[current_pitcher]
        if not ps['done'] and ps['consec'] < 2:
            return current_pitcher   # stays in
 
    # Need a new pitcher
    candidates = [
        p for p in playing
        if p in PITCHER_ELIGIBLE
        and not pitcher_state[p]['done']
        and p != current_pitcher
    ]
    if not candidates:
        # No eligible pitcher available — fall back to any eligible in playing
        candidates = [p for p in playing if p in PITCHER_ELIGIBLE]
    if not candidates:
        raise RuntimeError(f"Inning {inning}: No pitcher available among {playing}")
 
    # Prefer someone not yet burned (done=False)
    fresh = [p for p in candidates if not pitcher_state[p]['done']]
    return random.choice(fresh if fresh else candidates)
 
 
def _assign_remaining(players, positions):
    """
    Assign positions to players respecting NO_THIRD_BASE.
    Uses backtracking for correctness.
    """
    result = {}
 
    def backtrack(i):
        if i == len(players):
            return len(result) == len(players)
        p = players[i]
        random.shuffle(positions)   # already shuffled outside; fine here
        for pos in positions:
            if pos not in result.values() and can_play_position(p, pos):
                result[p] = pos
                if backtrack(i + 1):
                    return True
                del result[p]
        return False
 
    # Make positions a list we can track used slots
    pos_list = list(positions)
 
    def bt(i, used):
        if i == len(players):
            return True
        p = players[i]
        shuffled = pos_list[:]
        random.shuffle(shuffled)
        for pos in shuffled:
            if pos not in used and can_play_position(p, pos):
                result[p] = pos
                used.add(pos)
                if bt(i + 1, used):
                    return True
                del result[p]
                used.discard(pos)
        return False
 
    bt(0, set())
    return result
 
 
# ── main scheduler ────────────────────────────────────────────────────────────
 
def run_season():
    season_innings = defaultdict(int)   # cumulative innings per player
    all_games = {}
 
    for g in range(1, NUM_GAMES + 1):
        game = schedule_game(g, season_innings)
        all_games[g] = game
        # accumulate
        for inning_data in game.values():
            for player, pos in inning_data.items():
                if pos != 0:
                    season_innings[player] += 1
 
    return all_games, season_innings
 
 
# ── reporting ─────────────────────────────────────────────────────────────────
 
def print_season(all_games, season_innings):
    separator = "=" * 80
 
    print(separator)
    print("  BASEBALL DEFENSIVE ASSIGNMENTS  —  14 Games × 6 Innings")
    print(separator)
 
    for g in range(1, NUM_GAMES + 1):
        game = all_games[g]
        print(f"\n{'─'*80}")
        print(f"  GAME {g:>2}")
        print(f"{'─'*80}")
 
        # Header
        header = f"{'Inning':<8}" + "".join(f"{p:>10}" for p in PLAYERS)
        print(header)
        print("-" * len(header))
 
        for inning in range(1, NUM_INNINGS + 1):
            row = game[inning]
            line = f"{'Inn '+str(inning):<8}"
            for p in PLAYERS:
                pos = row.get(p, 0)
                label = POSITION_NAMES[pos][:7] if pos != 0 else "Bench"
                line += f"{label:>10}"
            print(line)
 
        # Per-game innings summary
        print()
        innings_per_player = defaultdict(int)
        for inning_data in game.values():
            for p, pos in inning_data.items():
                if pos != 0:
                    innings_per_player[p] += 1
        summary = "  Innings played: " + "  ".join(
            f"{p}={innings_per_player[p]}" for p in PLAYERS
        )
        print(summary)
        min_i = min(innings_per_player.values())
        max_i = max(innings_per_player.values())
        print(f"  (min={min_i}, max={max_i}  — spread ≤ 1: {'✓' if max_i - min_i <= 1 else '✗'})")
 
    # Season totals
    print(f"\n{separator}")
    print("  SEASON TOTALS  (innings played across all 14 games)")
    print(separator)
    total_possible = NUM_INNINGS * NUM_GAMES   # 84
    print(f"{'Player':<10} {'Innings':>8}  {'of ' + str(total_possible):>8}")
    print("-" * 30)
    for p in PLAYERS:
        print(f"{p:<10} {season_innings[p]:>8}  ({season_innings[p]/total_possible*100:.1f}%)")
 
    min_s = min(season_innings.values())
    max_s = max(season_innings.values())
    print(f"\nSeason spread: min={min_s}  max={max_s}  diff={max_s-min_s}")
    print(separator)
 
 
def verify_rules(all_games):
    """Sanity-check all hard rules and print a report."""
    errors = []
 
    for g, game in all_games.items():
        # Track pitcher state per game
        pitcher_consec  = defaultdict(int)
        pitcher_done    = set()
        prev_pitcher    = None
 
        for inning in range(1, NUM_INNINGS + 1):
            row = game[inning]
            playing = {p: pos for p, pos in row.items() if pos != 0}
 
            # Rule: exactly 9 on field
            if len(playing) != 9:
                errors.append(f"G{g} I{inning}: {len(playing)} players on field (need 9)")
 
            # Rule: no duplicate positions
            pos_used = list(playing.values())
            if len(pos_used) != len(set(pos_used)):
                errors.append(f"G{g} I{inning}: duplicate positions {pos_used}")
 
            # Rule: one position per inning (already enforced by structure)
 
            # Pitcher rules
            pitchers = [p for p, pos in playing.items() if pos == PITCHER_POS]
            if len(pitchers) != 1:
                errors.append(f"G{g} I{inning}: {len(pitchers)} pitchers")
            else:
                pitcher = pitchers[0]
                if pitcher not in PITCHER_ELIGIBLE:
                    errors.append(f"G{g} I{inning}: {pitcher} not pitcher-eligible")
                if pitcher in pitcher_done:
                    errors.append(f"G{g} I{inning}: {pitcher} re-entered as pitcher after removal")
                if pitcher == prev_pitcher:
                    pitcher_consec[pitcher] += 1
                else:
                    if prev_pitcher and prev_pitcher in playing and playing[prev_pitcher] != PITCHER_POS:
                        pitcher_done.add(prev_pitcher)
                    elif prev_pitcher and prev_pitcher not in playing:
                        pitcher_done.add(prev_pitcher)
                    pitcher_consec[pitcher] = 1
                if pitcher_consec[pitcher] > 2:
                    errors.append(f"G{g} I{inning}: {pitcher} pitched >2 consecutive innings")
                prev_pitcher = pitcher
 
            # Catcher rules
            catchers = [p for p, pos in playing.items() if pos == CATCHER_POS]
            if len(catchers) != 1:
                errors.append(f"G{g} I{inning}: {len(catchers)} catchers")
            else:
                if catchers[0] not in CATCHER_ELIGIBLE:
                    errors.append(f"G{g} I{inning}: {catchers[0]} not catcher-eligible")
 
            # No-3B rule
            third = [p for p, pos in playing.items() if pos == THIRD_POS]
            for p in third:
                if p in NO_THIRD_BASE:
                    errors.append(f"G{g} I{inning}: {p} playing 3B (not allowed)")
 
        # Per-game innings spread
        innings_count = defaultdict(int)
        for inning_data in game.values():
            for p, pos in inning_data.items():
                if pos != 0:
                    innings_count[p] += 1
        mn, mx = min(innings_count.values()), max(innings_count.values())
        if mx - mn > 1:
            errors.append(f"G{g}: innings spread {mx-mn} > 1  ({dict(innings_count)})")
 
    print("\n── Rule Verification ──")
    if errors:
        for e in errors:
            print(f"  ✗  {e}")
    else:
        print("  ✓  All rules satisfied across all 14 games.")
 
 
# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    all_games, season_innings = run_season()
    print_season(all_games, season_innings)
    verify_rules(all_games)
 
