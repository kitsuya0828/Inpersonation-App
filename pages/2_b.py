import streamlit as st
from audiorecorder import audiorecorder
import inspect
import textwrap
import pandas as pd
import pydeck as pdk
import librosa


from urllib.error import URLError


def mapping_demo():



    st.title("Audio Recorder")
    audio = audiorecorder("Click to record", "Recording...")
    try:
        if len(audio) > 0:

            # To play audio in frontend:
            st.audio(audio)

            # To save audio to a file:
            wav_file = open("audio.mp3", "wb")
            wav_file.write(audio.tobytes())
            x, sr = librosa.load("audio.mp3")
            # st.write(x, sr)
            feature = librosa.feature.spectral_centroid(x, sr)
            st.write(feature)
    except Exception as e:
        st.error(
            """
            **This demo requires internet access.**
            Connection error: %s
        """
            % e.reason
        )


st.set_page_config(page_title="Mapping Demo", page_icon="🌍")
st.markdown("# Mapping Demo")
st.sidebar.header("Mapping Demo")
st.write(
    """This demo shows how to use
[`st.pydeck_chart`](https://docs.streamlit.io/library/api-reference/charts/st.pydeck_chart)
to display geospatial data."""
)

mapping_demo()