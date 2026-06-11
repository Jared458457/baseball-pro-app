import streamlit as st
from engine import build_model, add_pitching, add_objective
from ortools.sat.python import cp_model
import pandas as pd

st.set_page_config(page_title="Pro Baseball Coach App", layout="wide")

st.title("⚾ Pro Baseball Coach App (Live)")

st.write("Generate a fully optimized 14-game season with constraints enforced.")

if st.button("Generate Season"):
    model, x = build_model()
    add_pitching(model, x)
    add_objective(model, x)

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

        st.success("Season generated successfully!")
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False)
        st.download_button("Download CSV", csv, "season.csv", "text/csv")
