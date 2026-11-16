import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

st.set_page_config(page_title="Fahrtenbuch", page_icon="🚗", layout="wide")

CSV_DATEI = "fahrtenbuch_daten.csv"

def lade_daten():
    if os.path.exists(CSV_DATEI):
        return pd.read_csv(CSV_DATEI)
    return pd.DataFrame(columns=[
        "Datum", "Startzeit", "Endzeit", "Startort", "Zielort", 
        "KM_Start", "KM_Ende", "Gefahrene_KM", "Zweck", "Kategorie"
    ])

if 'fahrt_gestartet' not in st.session_state:
    st.session_state.fahrt_gestartet = False
    st.session_state.start_zeit = None

st.title("🚗 Fahrtenbuch Außendienst")

menu = st.sidebar.radio("Modus", ["🚀 Schnell-Fahrt (Start/Stopp)", "📋 Übersicht & Export"])
df = lade_daten()

if menu == "🚀 Schnell-Fahrt (Start/Stopp)":
    # Letzten KM-Stand automatisch vorschlagen
    letzter_km = float(df["KM_Ende"].iloc[-1]) if not df.empty and "KM_Ende" in df.columns else 0.0

    if not st.session_state.fahrt_gestartet:
        st.subheader("Neue Fahrt beginnen")
        col1, col2 = st.columns(2)
        with col1:
            start_ort = st.text_input("Startort", value="Büro / Homeoffice")
        with col2:
            km_start = st.number_input("Tachostand Start (km):", min_value=0.0, step=1.0, value=letzter_km)

        if st.button("🚩 Fahrt Starten", type="primary", use_container_width=True):
            st.session_state.fahrt_gestartet = True
            st.session_state.start_zeit = datetime.now()
            st.session_state.start_ort = start_ort
            st.session_state.km_start = km_start
            st.rerun()
    else:
        st.info(f"Fahrt läuft seit **{st.session_state.start_zeit.strftime('%H:%M:%S')}** ab **{st.session_state.start_ort}** (Start-KM: {st.session_state.km_start})")
        
        col1, col2 = st.columns(2)
        with col1:
            ziel_ort = st.text_input("Zielort / Kunde", placeholder="z.B. Musterfirma GmbH")
            km_ende = st.number_input(
                "Tachostand Ankunft (km):", 
                min_value=st.session_state.km_start + 0.1, 
                step=1.0, 
                value=st.session_state.km_start + 10.0
            )
        with col2:
            kategorie = st.selectbox("Kategorie", ["Dienstlich", "Privat", "Arbeitsweg"])
            zweck = st.selectbox(
                "Zweck", 
                ["Betriebsbegehung", "Gefährdungsbeurteilung", "Unterweisung", "ASA-Sitzung", "Sonstiges"]
            )
            notiz = st.text_input("Bemerkung (optional)")

        if st.button("🏁 Fahrt Stoppen & Speichern", type="primary", use_container_width=True):
            end_zeit = datetime.now()
            gefahrene_km = round(km_ende - st.session_state.km_start, 1)
            zweck_komplett = f"{zweck} ({notiz})" if notiz else zweck

            neuer_eintrag = pd.DataFrame([{
                "Datum": date.today().strftime("%Y-%m-%d"),
                "Startzeit": st.session_state.start_zeit.strftime("%H:%M"),
                "Endzeit": end_zeit.strftime("%H:%M"),
                "Startort": st.session_state.start_ort,
                "Zielort": ziel_ort,
                "KM_Start": st.session_state.km_start,
                "KM_Ende": km_ende,
                "Gefahrene_KM": gefahrene_km,
                "Zweck": zweck_komplett,
                "Kategorie": kategorie
            }])

            df = pd.concat([df, neuer_eintrag], ignore_index=True)
            df.to_csv(CSV_DATEI, index=False)
            
            st.session_state.fahrt_gestartet = False
            st.success(f"Fahrt gespeichert! ({gefahrene_km} km)")
            st.rerun()

elif menu == "📋 Übersicht & Export":
    if not df.empty:
        # Kurze Kennzahlen oben anzeigen
        col1, col2 = st.columns(2)
        col1.metric("Gesamtkilometer", f"{df['Gefahrene_KM'].sum():.1f} km")
        dienst_km = df[df['Kategorie'] == 'Dienstlich']['Gefahrene_KM'].sum()
        col2.metric("Davon Dienstlich", f"{dienst_km:.1f} km")

        st.dataframe(df, use_container_width=True)
        
        # Semikolon als Trennzeichen für deutsches Excel
        csv_export = df.to_csv(index=False, sep=";").encode('utf-8-sig')
        st.download_button("📥 Export für Excel (CSV)", csv_export, "fahrtenbuch.csv", "text/csv")
    else:
        st.info("Noch keine Fahrten gespeichert.")
