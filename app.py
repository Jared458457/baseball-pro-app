import streamlit as st
from engine import build_model
from ortools.sat.python import cp_model
import pandas as pd

st.title("⚾ Pro Baseball Coach App")

if st.button("Generate Full Season"):
    model, x = build_model()

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30

    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):

        rows = []

        for g in range(14):
            for i in range(6):
                row = {"Game": g+1, "Inning": i+1}
                for pos in range(9):
                    for p in range(13):
                        if solver.Value(x[g,i,p,pos]):
                            row[pos] = f"P{p+1}"
                rows.append(row)

        df = pd.DataFrame(rows)
        st.dataframe(df)

        df.to_csv("season.csv", index=False)
        st.success("Season generated successfully")

def add_objective(model, x):

    total = []

    for p in range(13):
        tp = sum(x[g,i,p,pos]
                 for g in range(14)
                 for i in range(6)
                 for pos in range(9))
        total.append(tp)

    avg = (14*6*9)//13

    model.Minimize(sum((tp - avg)*(tp - avg) for tp in total))

def add_pitching(model, x):

    pitch_plan = [
        (3,4,6),(9,10,12),(13,3,4),(6,9,10),
        (12,13,3),(4,6,9),(10,12,13),(3,4,6),
        (9,10,12),(13,3,4),(6,9,10),(12,13,3),
        (4,6,9),(10,12,13)
    ]

    for g in range(14):
        p1,p2,p3 = pitch_plan[g]

        for i in range(6):
            if i < 2:
                model.Add(x[g,i,p1,0] == 1)
            elif i < 4:
                model.Add(x[g,i,p2,0] == 1)
            else:
                model.Add(x[g,i,p3,0] == 1)
