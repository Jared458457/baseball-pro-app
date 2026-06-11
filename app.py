import streamlit as st
from ortools.sat.python import cp_model
from engine import build_model, add_pitching, add_objective, add_position_constraints
import pandas as pd

st.title("⚾ Locked Pro Baseball Scheduler")

if st.button("Generate Season"):

    model, y, pos = build_model()

    add_pitching(model, y)
    add_objective(model, y)
    add_position_constraints(model, y, pos)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30

    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):

        rows = []

        for g in range(14):
            for i in range(6):
                row = {"Game": g+1, "Inning": i+1}

                players_in = []

                for p in range(13):
                    if solver.Value(y[g,i,p]):
                        players_in.append(p)

                # assign positions cleanly
                for idx, p in enumerate(players_in):
                    row[f"slot_{idx}"] = f"P{p+1}"

                rows.append(row)

        st.success("Perfectly locked schedule generated")
        st.dataframe(pd.DataFrame(rows))
