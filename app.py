import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# Seitenkonfiguration
st.set_page_config(
    page_title="Fahrtenbuch – Arbeitssicherheit Außendienst",
    page_icon="🚗",
    layout="wide"
)

DATA_FILE = "fahrtenbuch_daten.csv"
FAVORITEN_FILE = "fahrtenbuch_favoriten.csv"

# Daten laden
def lade_daten():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Datum'] = pd.to_datetime(df['Datum']).dt.date
        return df
    else:
        return pd.DataFrame(columns=[
            "ID", "Datum", "Fahrzeug", "Start", "Ziel", "Kilometer", "Kategorie", "Zweck", "Notiz"
        ])

def speichere_daten(df):
    df.to_csv(DATA_FILE, index=False)

def lade_favoriten():
    if os.path.exists(FAVORITEN_FILE):
        return pd.read_csv(FAVORITEN_FILE)['Standort'].tolist()
    else:
        return ["Büro / Homeoffice", "Hauptwerk", "Kunde A", "Kunde B"]

def speichere_favoriten(favs):
    pd.DataFrame({'Standort': favs}).to_csv(FAVORITEN_FILE, index=False)

df = lade_daten()
favoriten = lade_favoriten()

# Titel & Beschreibung
st.title("🚗 Digitales Fahrtenbuch (Außendienst)")
st.markdown("Maßgeschneidert für Fachkräfte für Arbeitssicherheit – 100% kostenlos, ohne Abos & datenschutzkonform.")

# Sidebar Navigation
menu = st.sidebar.radio("Navigation", ["➕ Neue Fahrt erfassen", "📋 Fahrtenübersicht", "⭐ Stammstrecken / Orte", "📊 Auswertung & Export"])

# -------------------------------------------------------------
# 1. NEUE FAHRT ERFASSEN
# -------------------------------------------------------------
if menu == "➕ Neue Fahrt erfassen":
    st.header("Neue Fahrt eintragen")

    with st.form("fahrt_form"):
        col1, col2 = st.columns(2)

        with col1:
            datum = st.date_input("Datum", value=date.today())
            fahrzeug = st.text_input("Fahrzeug / Kennzeichen", value="Firmierung / PKW 1")
            kategorie = st.selectbox("Kategorie", ["Dienstlich", "Privat", "Wohnung - Arbeitsstätte"])

        with col2:
            zweck_optionen = [
                "Betriebsbegehung",
                "Gefährdungsbeurteilung vor Ort",
                "Sicherheitsunterweisung / Schulung",
                "ASA-Sitzung (Arbeitssicherheitsausschuss)",
                "Unfalluntersuchung",
                "Beratung Arbeitsschutz",
                "Sonstiges"
            ]
            zweck_wahl = st.selectbox("Zweck-Vorlagen", zweck_optionen)
            zweck_custom = st.text_input("Zweck (Details)", value=zweck_wahl)
            kilometer = st.number_input("Gefahrene Kilometer (km)", min_value=0.1, step=0.5, value=15.0)

        st.markdown("---")
        col3, col4 = st.columns(2)
        with col3:
            start = st.selectbox("Startort", options=favoriten, index=0)
            start_custom = st.text_input("Oder Startadresse manuell eingeben (optional)", value="")
        with col4:
            ziel = st.selectbox("Zielort", options=favoriten, index=min(1, len(favoriten)-1))
            ziel_custom = st.text_input("Oder Zieladresse manuell eingeben (optional)", value="")

        notiz = st.text_area("Notizen / Ansprechpartner vor Ort (optional)", placeholder="z.B. Begehung Halle 2 mit Herrn Müller")

        submitted = st.form_submit_button("Fahrt speichern 💾", use_container_width=True)

        if submitted:
            final_start = start_custom if start_custom else start
            final_ziel = ziel_custom if ziel_custom else ziel

            neuer_eintrag = pd.DataFrame([{
                "ID": len(df) + 1,
                "Datum": datum,
                "Fahrzeug": fahrzeug,
                "Start": final_start,
                "Ziel": final_ziel,
                "Kilometer": float(kilometer),
                "Kategorie": kategorie,
                "Zweck": zweck_custom,
                "Notiz": notiz if notiz else ""
            }])

            df = pd.concat([df, neuer_eintrag], ignore_index=True)
            speichere_daten(df)
            st.success(f"Fahrt erfolgreich gespeichert! ({kilometer} km von {final_start} nach {final_ziel})")

# -------------------------------------------------------------
# 2. FAHRTENÜBERSICHT
# -------------------------------------------------------------
elif menu == "📋 Fahrtenübersicht":
    st.header("Bisherige Fahrten")

    if df.empty:
        st.info("Noch keine Fahrten eingetragen.")
    else:
        # Filteroptionen
        col1, col2 = st.columns(2)
        with col1:
            filter_kat = st.multiselect("Nach Kategorie filtern", df['Kategorie'].unique(), default=df['Kategorie'].unique())
        with col2:
            suche = st.text_input("Suche (Ziel, Zweck, Notiz)...")

        gefiltert = df[df['Kategorie'].isin(filter_kat)]
        if suche:
            gefiltert = gefiltert[
                gefiltert['Ziel'].str.contains(suche, case=False, na=False) |
                gefiltert['Zweck'].str.contains(suche, case=False, na=False) |
                gefiltert['Notiz'].str.contains(suche, case=False, na=False) |
                gefiltert['Start'].str.contains(suche, case=False, na=False)
            ]

        st.dataframe(gefiltert, use_container_width=True)

        # Eintrag löschen
        st.markdown("### Eintrag löschen")
        loesch_id = st.number_input("ID der Fahrt zum Löschen", min_value=1, max_value=int(df['ID'].max()) if not df.empty else 1, step=1)
        if st.button("Ausgewählte Fahrt löschen 🗑️"):
            df = df[df['ID'] != loesch_id]
            speichere_daten(df)
            st.success(f"Fahrt mit ID {loesch_id} gelöscht!")
            st.rerun()

# -------------------------------------------------------------
# 3. FAVORITEN / ORTE
# -------------------------------------------------------------
elif menu == "⭐ Stammstrecken / Orte":
    st.header("Stamm-Standorte verwalten")
    st.markdown("Füge häufig genutzte Orte (z.B. Hauptkunden, Büro, Labor) hinzu, damit du sie bei der Erfassung direkt auswählen kannst.")

    col1, col2 = st.columns(2)
    with col1:
        neuer_ort = st.text_input("Neuer Standort / Kunde")
        if st.button("Standort hinzufügen ➕"):
            if neuer_ort and neuer_ort not in favoriten:
                favoriten.append(neuer_ort)
                speichere_favoriten(favoriten)
                st.success(f"Standort '{neuer_ort}' hinzugefügt!")
                st.rerun()

    with col2:
        st.markdown("### Aktuelle Standorte:")
        for i, ort in enumerate(favoriten):
            st.write(f"- {ort}")

        ort_zu_loeschen = st.selectbox("Standort zum Löschen", options=favoriten)
        if st.button("Standort entfernen ❌"):
            if len(favoriten) > 1:
                favoriten.remove(ort_zu_loeschen)
                speichere_favoriten(favoriten)
                st.success(f"Standort '{ort_zu_loeschen}' entfernt!")
                st.rerun()
            else:
                st.warning("Es muss mindestens ein Standort erhalten bleiben.")

# -------------------------------------------------------------
# 4. AUSWERTUNG & EXPORT
# -------------------------------------------------------------
elif menu == "📊 Auswertung & Export":
    st.header("Auswertung & Finanzamt-Export")

    if df.empty:
        st.info("Keine Daten für eine Auswertung vorhanden.")
    else:
        col1, col2, col3 = st.columns(3)

        gesamtkilometer = df['Kilometer'].sum()
        dienstlich_km = df[df['Kategorie'] == 'Dienstlich']['Kilometer'].sum()
        privat_km = df[df['Kategorie'] == 'Privat']['Kilometer'].sum()

        with col1:
            st.metric("Gesamtkilometer", f"{gesamtkilometer:.1f} km")
        with col2:
            st.metric("Dienstliche Kilometer", f"{dienstlich_km:.1f} km")
        with col3:
            st.metric("Private Kilometer", f"{privat_km:.1f} km")

        st.markdown("---")
        st.subheader("Export für Buchhaltung / Finanzamt")

        # CSV Export
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Fahrtenbuch als CSV / Excel-kompatibel herunterladen",
            data=csv,
            file_name=f"fahrtenbuch_{date.today().strftime('%Y-%m-%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
