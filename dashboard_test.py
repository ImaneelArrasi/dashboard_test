# -*- coding: utf-8 -*-
"""
Created on Mon May 19 15:56:03 2025

@author: ielar
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from scipy.signal import find_peaks, butter, filtfilt



# Pagina configuratie voor maximale breedte
st.set_page_config(
    page_title="Patiënt Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Dashboard patient")

# === DATA INLEZEN ===
df = pd.read_csv("gegevens.csv")

# === R-PIEKEN, HR & HRV BEREKENING ===
pieken = find_peaks(df['ecg'], height=0.6 * max(df['ecg']))[0]
t_pieken = df['timestamp'].iloc[pieken].values
rr = np.diff(t_pieken)

bpm = 60 / rr
gem_bpm = np.mean(bpm)
def kleur_hartslag(bpm):
    if bpm < 50:
        return "blue"
    elif bpm > 100:
        return "red"
    else:
        return "green"

gem_bpm = np.mean(60 / rr)
kleur = kleur_hartslag(gem_bpm)

# HRV: RMSSD
rmssd = np.sqrt(np.mean(np.diff(rr)**2)) * 100
fig_rmssd = go.Figure(go.Indicator(
    mode="gauge+number",
    value=rmssd,
    title={'text': "HRV"},
    gauge={'axis': {'range': [0, 100]},
           'steps': [{'range': [0, 25], 'color': "red"},
                     {'range': [25, 50], 'color': "orange"},
                     {'range': [50, 75], 'color': "lightgreen"},
                     {'range': [75, 100], 'color': "green"}],
           'threshold': {'line': {'color': "black", 'width': 4}, 'value': rmssd}}
))


# === ADEMHALINGSFREQUENTIE SCHATTING ===
def ademfrequentie(ecg, fs):
    b, a = butter(2, 0.5 / (fs / 2), btype='low')
    ademgolf = filtfilt(b, a, ecg)
    zero_crossings = ((np.diff(np.sign(ademgolf)) > 0).sum())
    ademhalingen_per_min = zero_crossings * (60 / (len(ecg) / fs)) / 2
    return round(ademhalingen_per_min, 1)

ademfreq = ademfrequentie(df['ecg'], fs=1024)

# === TEMPERATUURPLOT ===
gem_temp = df['temperatuur'].iloc[-1]  # Of .mean() als je het gemiddelde wilt
def kleur_temperatuur(temp):
    if temp < 30:
        return "blue"     # te koud
    elif 30 <= temp <= 36:
        return "green"    # normaal
    elif 36 < temp <= 38:
        return "orange"   # licht verhoogd
    else:
        return "red"      # te hoog

# === ECGPLOT ===
fig_ecg, ax_ecg = plt.subplots(figsize=(12,3))
ax_ecg.plot(df['timestamp'], df['ecg'], color='blue')
ax_ecg.set_title("ECG Signaal")
ax_ecg.set_xlabel("Tijd (s)")
ax_ecg.set_ylabel("Amplitude")
ax_ecg.grid(True)

# === BEWEGINGSINTENSITEIT (gesimuleerd) ===
tijdblokken = df['timestamp'] // 5 * 5
bewegingsintensiteit = pd.Series(np.abs(np.gradient(df['ecg'])), name="intensiteit")
df_beweging = pd.DataFrame({'tijdblok': tijdblokken, 'intensiteit': bewegingsintensiteit})
intens_per_blok = df_beweging.groupby('tijdblok').mean().reset_index()

fig_beweging, ax_beweging = plt.subplots()
ax_beweging.plot(intens_per_blok['tijdblok'], intens_per_blok['intensiteit'], marker='o')
ax_beweging.set_title("📈 Bewegingsintensiteit")
ax_beweging.set_xlabel("Tijd (s)")
ax_beweging.set_ylabel("Intensiteit")

# === DASHBOARD WEERGAVE ===
 # === SIDEBAR ===
st.sidebar.title("📋 Menu")
pagina = st.sidebar.radio("Ga naar", ["Dashboard", "Instructie"])

if pagina == "Dashboard": 
    #with st.container():
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("💓 HRV")
        st.plotly_chart(fig_rmssd, use_container_width=True)
        
    with col2:
        st.subheader("🌡️ Gemeten Huidtemperatuur")
        kleur_temp = kleur_temperatuur(gem_temp)
        # Temperatuur als getal weergeven
        st.markdown(
        f"<h1 style='color:{kleur_temp}; font-size:64px; text-align:center;'> {gem_temp:.1f} °C</h1>",
        unsafe_allow_html=True)
        
        
    with col3:
        st.metric("🌬️ Ademfrequentie", f"{ademfreq} /min") 
        
    with st.container():
         col4, col5 = st.columns(2)
    
    with col4:
        st.subheader("📊 Bewegingsintensiteit")
        st.pyplot(fig_beweging)
        
   
    with col5:
        st.subheader("😃 Beleving van de Beweging")
        smiley = st.select_slider("Beleving", options=["😴", "🙂", "😐", "😰", "😵"])
        activiteit = st.text_input("Welke beweging deed je?")
        tijdstip = st.time_input("Tijdstip van uitvoering")
        
    with st.container():
        col6, col7 = st.columns(2)
    with col6:
        kleur = kleur_hartslag(gem_bpm)
        st.subheader("Gemiddelde Hartslag (ECG)")
        st.markdown(f"<h1 style='color:{kleur}; font-size:72px; text-align:center;'>❤️ {int(gem_bpm)} BPM</h1>",
        unsafe_allow_html=True
        
    )
    with col7:
            st.subheader("Ruwe ECG")
            st.pyplot(fig_ecg)
    
elif pagina == "Instructie":
    st.title("📘 Instructies")
    st.markdown("""
    1.	Stappenplan hoe te handelen mits het niet goed gaat./ bij versechtering alert zijn.
    2.	Hoe huisarts/cardioloog te contacteren
    3.	Stappenplan monteren van sensor aan lichaam?
    4.	Inwerk stappenplan/programma
    5.	Reserve onderdelen opvragen
    """)
else: ('geen pagina gevonden')

st.sidebar.markdown("---")  # optioneel: scheidingslijn

st.sidebar.subheader("📅 Geschiedenis")
st.sidebar.selectbox("Bekijk meting van:", ["Vandaag", "Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"])

st.sidebar.subheader("💬 Communicatie & Input")
bericht = st.sidebar.text_area("Bericht aan cardioloog/huisarts", placeholder="Typ hier je bericht...")
vraag = st.sidebar.text_input("Stel een vraag", placeholder="Bijv. Hoe was mijn ademhaling?")

