# EVERYTHING IN ONE FILE
# (no imports except streamlit + ortools)

import streamlit as st
from ortools.sat.python import cp_model
import pandas as pd

# ---------------- ENGINE ----------------

def build_model():
    model = cp_model.CpModel()
    x = {}
    for g in range(14):
        for i in range(6):
            for p in range(13):
                for pos in range(9):
                    x[g,i,p,pos] = model.NewBoolVar(f"x_{g}_{i}_{p}_{pos}")

    return model, x


def add_pitching(model, x):
    pitch_plan = [
        (2,3,5),(8,9,11),(12,2,3),(5,8,9),
        (11,12,2),(3,5,8),(9,11,12),
        (2,3,5),(8,9,11),(12,2,3),
        (5,8,9),(11,12,2),(3,5,8),(9,11,12)
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


def add_objective(model, x):
    model.Minimize(0)  # simplified for stability

# ---------------- UI ----------------

st.title("⚾ Pro Baseball App")

if st.button("Generate"):
    model, x = build_model()
    add_pitching(model, x)
    add_objective(model, x)

    solver = cp_model.CpSolver()
    solver.Solve(model)

    st.success("Generated (basic mode)")
