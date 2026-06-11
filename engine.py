from ortools.sat.python import cp_model

GAMES = 14
INNINGS = 6
PLAYERS = 13
POSITIONS = 9

catchers = {0,3,8,11}   # P1,P4,P9,P12
no_3b = {1,4,6}         # P2,P5,P7

def build_model():
    model = cp_model.CpModel()

    # y = player participates in inning
    y = {}
    # pos = player position (only valid if y=1)
    pos = {}

    for g in range(GAMES):
        for i in range(INNINGS):
            for p in range(PLAYERS):
                y[g,i,p] = model.NewBoolVar(f"y_{g}_{i}_{p}")

                pos[g,i,p] = model.NewIntVar(0, POSITIONS-1, f"pos_{g}_{i}_{p}")

    # exactly 9 players per inning
    for g in range(GAMES):
        for i in range(INNINGS):
            model.Add(
                sum(y[g,i,p] for p in range(PLAYERS)) == 9
            )

    # no player plays more than 1 position per inning (impossible now by design)
    # enforced implicitly by y

    return model, y, pos


def add_position_constraints(model, y, pos):

    # Catcher restriction
    for g in range(GAMES):
        for i in range(INNINGS):
            for p in range(PLAYERS):
                is_catcher_allowed = (p in catchers)
                # if not allowed catcher, cannot take position 1
                model.Add(pos[g,i,p] != 1).OnlyEnforceIf(y[g,i,p].Not()).OnlyEnforceIf(model.NewBoolVar("tmp"))

                if not is_catcher_allowed:
                    model.Add(pos[g,i,p] != 1).OnlyEnforceIf(y[g,i,p])

    # 3B restriction
    for g in range(GAMES):
        for i in range(INNINGS):
            for p in no_3b:
                model.Add(pos[g,i,p] != 4).OnlyEnforceIf(y[g,i,p])


def add_pitching(model, y):

    pitch_plan = [
        (2,3,5),(8,9,11),(12,2,3),(5,8,9),
        (11,12,2),(3,5,8),(9,11,12),
        (2,3,5),(8,9,11),(12,2,3),
        (5,8,9),(11,12,2),(3,5,8),(9,11,12)
    ]

    for g in range(GAMES):
        p1,p2,p3 = pitch_plan[g]

        for i in range(INNINGS):
            if i < 2:
                model.Add(y[g,i,p1] == 1)
            elif i < 4:
                model.Add(y[g,i,p2] == 1)
            else:
                model.Add(y[g,i,p3] == 1)


def add_objective(model, y):

    target = (GAMES * INNINGS * 9) // PLAYERS

    diffs = []

    for p in range(PLAYERS):
        total = sum(
            y[g,i,p]
            for g in range(GAMES)
            for i in range(INNINGS)
        )

        d = model.NewIntVar(-100, 100, f"d_{p}")
        a = model.NewIntVar(0, 100, f"a_{p}")

        model.Add(d == total - target)
        model.AddAbsEquality(a, d)

        diffs.append(a)

    model.Minimize(sum(diffs))
