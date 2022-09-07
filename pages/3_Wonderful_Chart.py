import streamlit as st
import time
import librosa
import numpy as np
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(page_title="グラフ", page_icon="👍")

y1, sr1 = librosa.load("static/theme/Meow.wav")
y2, sr2 = librosa.load("static/theme/Dog animals080.wav")

fig = go.Figure()
fig.add_trace(go.Scatter(x=[i for i in range(len(y1))],
              y=y1,
              name='cat'))
fig.add_trace(go.Scatter(x=[i for i in range(len(y2))],
              y=y2,
              name='dog'))
st.plotly_chart(fig, use_container_width=True)

def plotting_demo():
    # progress_bar = st.sidebar.progress(0)
    # status_text = st.sidebar.empty()
    last_rows = np.random.randn(1, 1)
    chart = st.line_chart(last_rows)

    for i in range(1, 101):
        new_rows = last_rows[-1, :] + np.random.randn(5, 1).cumsum(axis=0)
        print(new_rows)
        break
        # status_text.text("%i%% Complete" % i)
        chart.add_rows(new_rows)
        # progress_bar.progress(i)
        last_rows = new_rows
        time.sleep(0.02)

    # progress_bar.empty()

    # Streamlit widgets automatically run the script from top to bottom. Since
    # this button is not connected to any other logic, it just causes a plain
    # rerun.
    st.button("Re-run")



st.markdown("# グラフ")
st.sidebar.header("グラフ")
st.write(
    """This demo illustrates a combination of plotting and animation with
Streamlit. We're generating a bunch of random numbers in a loop for around
5 seconds. Enjoy!"""
)

# plotting_demo()