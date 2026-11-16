  import streamlit as st
  import pandas as pd
  from datetime import datetime, date
  import os

  st.set_page_config(page_title="Fahrtenbuch", page_icon="🚗", layout="wide")

  # Session State für Start-Zeit und Start-Ort
  if 'fahrt_gestartet' not in st.session_state:
      st.session_state.fahrt_gestartet = False
      st.session_state.start_zeit = None

  st.title("🚗 Fahrtenbuch Außendienst")

  menu = st.sidebar.radio("Modus", ["🚀 Schnell-Fahrt (Start/Stopp)", "📋 Übersicht & Export"])

  if menu == "🚀 Schnell-Fahrt (Start/Stopp)":
      if not st.session_state.fahrt_gestartet:
          if st.button("🚩 Fahrt Starten", type="primary", use_container_width=True):
              st.session_state.fahrt_gestartet = True
              st.session_state.start_zeit = datetime.now()
              st.success("Fahrt wurde gestartet! Gute Reise.")
              st.rerun()
      else:
          st.info(f"Fahrt läuft seit: {st.session_state.start_zeit.strftime('%H:%M:%S')}")
          km = st.number_input("Kilometer bei Ankunft:", min_value=0.1, step=1.0, value=10.0)
          zweck = st.selectbox("Zweck", ["Betriebsbegehung", "Gefährdungsbeurteilung", "Unterweisung", "Sonstiges"])

          if st.button("🏁 Fahrt Stoppen & Speichern", type="primary", use_container_width=True):
              # Speichern in CSV
              neuer_eintrag = pd.DataFrame([{
                  "ID": 1, "Datum": date.today(), "Kilometer": km, "Zweck": zweck, "Kategorie": "Dienstlich"
              }])
              if os.path.exists("fahrtenbuch_daten.csv"):
                  df = pd.read_csv("fahrtenbuch_daten.csv")
                  df = pd.concat([df, neuer_eintrag], ignore_index=True)
              else:
                  df = neuer_eintrag
              df.to_csv("fahrtenbuch_daten.csv", index=False)

              st.session_state.fahrt_gestartet = False
              st.success("Fahrt gespeichert!")
              st.rerun()

  elif menu == "📋 Übersicht & Export":
      if os.path.exists("fahrtenbuch_daten.csv"):
          df = pd.read_csv("fahrtenbuch_daten.csv")
          st.dataframe(df, use_container_width=True)
          st.download_button("📥 Export als CSV", df.to_csv(index=False).encode('utf-8'), "fahrtenbuch.csv", "text/csv")
      else:
          st.info("Noch keine Fahrten gespeichert.")
