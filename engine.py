from ortools.sat.python import cp_model

games = 14
innings = 6
players = 13
positions = 9

catchers = [0,3,8,11]   # P1,P4,P9,P12
no_3b = [1,4,6]         # P2,P5,P7
pitchers = [2,3,5,8,9,11,12]

def build_model():
    model = cp_model.CpModel()

    x = {}

    for g in range(games):
        for i in range(innings):
            for p in range(players):
                for pos in range(positions):
                    x[g,i,p,pos] = model.NewBoolVar(f"x_{g}_{i}_{p}_{pos}")

# Each position filled by exactly one player
    for g in range(games):
        for i in range(innings):
            for pos in range(positions):
                model.Add(
                    sum(x[g,i,p,pos] for p in range(players)) == 1
                )    

# Each player plays at most one position per inning (CRITICAL FIX)
    for g in range(games):
        for i in range(innings):
            for p in range(players):
                model.Add(
                    sum(x[g,i,p,pos] for pos in range(positions)) <= 1
                )
    
    # Each player plays 4–5 innings per game
    for g in range(games):
        for p in range(players):
            play = sum(x[g,i,p,pos]
                       for i in range(innings)
                       for pos in range(positions))
            model.Add(play >= 4)
            model.Add(play <= 5)

    # Catcher restriction
    for g in range(games):
        for i in range(innings):
            for p in range(players):
                if p not in catchers:
                    model.Add(x[g,i,p,1] == 0)

    # 3B restriction
    for g in range(games):
        for i in range(innings):
            for p in no_3b:
                model.Add(x[g,i,p,4] == 0)

    return model, x


def add_pitching(model, x):
    pitch_plan = [
        (2,3,5),(8,9,11),(12,2,3),(5,8,9),
        (11,12,2),(3,5,8),(9,11,12),(2,3,5),
        (8,9,11),(12,2,3),(5,8,9),(11,12,2),
        (3,5,8),(9,11,12)
    ]

    for g in range(games):
        p1,p2,p3 = pitch_plan[g]

        for i in range(innings):
            if i < 2:
                model.Add(x[g,i,p1,0] == 1)
            elif i < 4:
                model.Add(x[g,i,p2,0] == 1)
            else:
                model.Add(x[g,i,p3,0] == 1)

from ortools.sat.python import cp_model

def add_objective(model, x):

    total = []

    games = 14
    innings = 6
    players = 13
    positions = 9

    target = (games * innings * positions) // players  # ~58

    deviations = []

    for p in range(players):

        tp = sum(
            x[g,i,p,pos]
            for g in range(games)
            for i in range(innings)
            for pos in range(positions)
        )

        # introduce integer slack variables
        diff = model.NewIntVar(-100, 100, f"diff_{p}")
        abs_diff = model.NewIntVar(0, 100, f"abs_diff_{p}")

        model.Add(diff == tp - target)

        model.AddAbsEquality(abs_diff, diff)

        deviations.append(abs_diff)

    model.Minimize(sum(deviations))

