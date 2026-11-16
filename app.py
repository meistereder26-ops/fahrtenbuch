import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

st.set_page_config(page_title="Fahrtenbuch", page_icon="🚗", layout="centered")

conn = st.connection("gsheets", type=GSheetsConnection)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1_Yinpa19hnDXZcHnlx3pR_N2HKKZlkQvitakKlq2dXA/edit?gid=0#gid=0"
SPALTEN = [
    "Datum", "Startzeit", "Endzeit", "Startort", "Zielort",
    "KM_Start", "KM_Ende", "Gefahrene_KM", "Zweck", "Kategorie"
]

def lade_daten():
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Tabellenblatt1", ttl=0)
        if df.empty or "Datum" not in df.columns:
            return pd.DataFrame(columns=SPALTEN)
        return df.dropna(how="all")
    except Exception as e:
        st.error(f"Lesefehler: {e}")
        return pd.DataFrame(columns=SPALTEN)

st.title("🚗 Fahrtenbuch Außendienst")

menu = st.radio("Ansicht", ["🚀 Fahrt erfassen", "📋 Übersicht & Export"], horizontal=True)
df = lade_daten()

if menu == "🚀 Fahrt erfassen":
    fahrt_laeuft = False
    if not df.empty and pd.isna(df.iloc[-1]["Endzeit"]):
        fahrt_laeuft = True
        aktuelle_fahrt = df.iloc[-1]

    if not fahrt_laeuft:
        st.subheader("Neue Fahrt starten")
        letzter_km = (
            float(df["KM_Ende"].dropna().iloc[-1])
            if not df.empty and not df["KM_Ende"].dropna().empty
            else 0.0
        )

        start_ort = st.text_input("Startort", value="Büro / Homeoffice")
        km_start = st.number_input("Tachostand Start (km):", min_value=0.0, step=1.0, value=letzter_km)

        if st.button("🚩 Fahrt Starten", type="primary", use_container_width=True):
            neue_zeile = pd.DataFrame([{
                "Datum": date.today().strftime("%Y-%m-%d"),
                "Startzeit": datetime.now().strftime("%H:%M"),
                "Endzeit": None,
                "Startort": start_ort,
                "Zielort": "",
                "KM_Start": km_start,
                "KM_Ende": None,
                "Gefahrene_KM": None,
                "Zweck": "",
                "Kategorie": "Dienstlich"
            }])
            df_neu = pd.concat([df, neue_zeile], ignore_index=True)
            try:
                conn.update(spreadsheet=SHEET_URL, worksheet="Tabellenblatt1", data=df_neu)
                st.rerun()
            except Exception as e:
                st.error(f"Schreibfehler: {e}")

    else:
        st.warning(
            f"Fahrt läuft seit **{aktuelle_fahrt['Startzeit']}** ab **{aktuelle_fahrt['Startort']}** "
            f"(Start: {aktuelle_fahrt['KM_Start']} km)"
        )

        ziel_ort = st.text_input("Zielort / Kunde", placeholder="z.B. Musterfirma GmbH")
        km_ende = st.number_input(
            "Tachostand Ankunft (km):",
            min_value=float(aktuelle_fahrt["KM_Start"]) + 0.1,
            step=1.0,
            value=float(aktuelle_fahrt["KM_Start"]) + 10.0
        )
        kategorie = st.selectbox("Kategorie", ["Dienstlich", "Privat", "Arbeitsweg"])
        zweck = st.selectbox(
            "Zweck",
            ["Betriebsbegehung", "Gefährdungsbeurteilung", "Unterweisung", "ASA-Sitzung", "Sonstiges"]
        )
        notiz = st.text_input("Bemerkung (optional)")

        if st.button("🏁 Fahrt Stoppen & Speichern", type="primary", use_container_width=True):
            km_start_val = float(aktuelle_fahrt["KM_Start"])
            gefahrene_km = round(km_ende - km_start_val, 1)
            zweck_komplett = f"{zweck} ({notiz})" if notiz else zweck

            idx = df.index[-1]
            df.at[idx, "Endzeit"] = datetime.now().strftime("%H:%M")
            df.at[idx, "Zielort"] = ziel_ort
            df.at[idx, "KM_Ende"] = km_ende
            df.at[idx, "Gefahrene_KM"] = gefahrene_km
            df.at[idx, "Zweck"] = zweck_komplett
            df.at[idx, "Kategorie"] = kategorie

            try:
                conn.update(spreadsheet=SHEET_URL, worksheet="Tabellenblatt1", data=df)
                st.success(f"Fahrt gespeichert! ({gefahrene_km} km)")
                st.rerun()
            except Exception as e:
                st.error(f"Schreibfehler: {e}")

elif menu == "📋 Übersicht & Export":
    if not df.empty:
        abgeschlossene = df.dropna(subset=["Endzeit"])
        col1, col2 = st.columns(2)
        col1.metric("Gesamtkilometer", f"{abgeschlossene['Gefahrene_KM'].sum():.1f} km")
        dienst_km = abgeschlossene[abgeschlossene["Kategorie"] == "Dienstlich"]["Gefahrene_KM"].sum()
        col2.metric("Davon Dienstlich", f"{dienst_km:.1f} km")

        st.dataframe(df, use_container_width=True)

        csv_export = df.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button(
            "📥 Export als CSV",
            csv_export,
            "fahrtenbuch.csv",
            "text/csv",
            use_container_width=True
        )
    else:
        st.info("Noch keine Fahrten gespeichert.")
