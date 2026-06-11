from ortools.sat.python import cp_model

players = list(range(13))
games = 14
innings = 6
positions = 9

catchers = {1,4,9,12}
no_3b = {2,5,7}
pitchers = [3,4,6,9,10,12,13]

def build_model():

    model = cp_model.CpModel()

    x = {}

    # x[g,i,p,pos]
    for g in range(games):
        for i in range(innings):
            for p in players:
                for pos in range(positions):
                    x[g,i,p,pos] = model.NewBoolVar(f"x_{g}_{i}_{p}_{pos}")

    # one player per position per inning
    for g in range(games):
        for i in range(innings):
            for pos in range(positions):
                model.Add(sum(x[g,i,p,pos] for p in players) == 1)

    # each player plays 4–5 innings per game
    for g in range(games):
        for p in players:
            play = sum(x[g,i,p,pos] for i in range(innings) for pos in range(positions))
            model.Add(play >= 4)
            model.Add(play <= 5)

    # catcher restriction
    for g in range(games):
        for i in range(innings):
            for p in players:
                if p not in catchers:
                    model.Add(x[g,i,p,1] == 0)

    # 3B restriction
    for g in range(games):
        for i in range(innings):
            for p in no_3b:
                model.Add(x[g,i,p,4] == 0)

    return model, x
