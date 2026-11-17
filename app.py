import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_js_eval import get_geolocation
import requests
import pandas as pd
from datetime import datetime, date

st.set_page_config(page_title="Fahrtenbuch", page_icon="🚗", layout="centered")

conn = st.connection("gsheets", type=GSheetsConnection)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1_Yinpa19hnDXZcHnlx3pR_N2HKKZlkQvitakKlq2dXA/edit?gid=0#gid=0"
TEXT_SPALTEN = ["Datum", "Startzeit", "Endzeit", "Startort", "Zielort", "Zweck", "Kategorie", "Start_GPS"]
ZAHL_SPALTEN = ["KM_Start", "KM_Ende", "Gefahrene_KM"]
SPALTEN = [
    "Datum", "Startzeit", "Endzeit", "Startort", "Zielort",
    "KM_Start", "KM_Ende", "Gefahrene_KM", "Zweck", "Kategorie", "Start_GPS"
]

# Sauberes Zurücksetzen der Felder VOR dem Rendern der Widgets
if st.session_state.get("reset_form", False):
    for key in ["ziel_ort_text", "km_ende_input", "gps_berechnete_km", "start_gps_coords"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state["gps_start_aktiv"] = False
    st.session_state["gps_ziel_aktiv"] = False
    st.session_state["reset_form"] = False

def adresse_aus_gps(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
        headers = {"User-Agent": "FahrtenbuchStreamlitApp/1.0"}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            addr = res.json().get("address", {})
            strasse = addr.get("road", "")
            hausnr = addr.get("house_number", "")
            plz = addr.get("postcode", "")
            ort = addr.get("city") or addr.get("town") or addr.get("village") or ""
            strasse_komplett = f"{strasse} {hausnr}".strip()
            ort_komplett = f"{plz} {ort}".strip()
            teile = [t for t in [strasse_komplett, ort_komplett] if t]
            if teile:
                return ", ".join(teile)
    except Exception:
        pass
    return f"GPS: {lat:.5f}, {lon:.5f}"

def berechne_strassen_km(lat1, lon1, lat2, lon2):
    try:
        url = f"https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            daten = res.json()
            if daten.get("routes"):
                meter = daten["routes"][0]["distance"]
                return round(meter / 1000.0, 1)
    except Exception:
        pass
    return None

def lade_daten():
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Tabellenblatt1", ttl=0)
        if df.empty or "Datum" not in df.columns:
            df = pd.DataFrame(columns=SPALTEN)
        else:
            df = df.dropna(how="all")
            for col in SPALTEN:
                if col not in df.columns:
                    df[col] = None
        for col in TEXT_SPALTEN:
            df[col] = df[col].astype("object")
        for col in ZAHL_SPALTEN:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df[SPALTEN]
    except Exception as e:
        st.error(f"Lesefehler: {e}")
        return pd.DataFrame(columns=SPALTEN)

st.title("🚗 Fahrtenbuch Außendienst")

menu = st.radio("Ansicht", ["🚀 Fahrt erfassen", "📋 Übersicht & Export"], horizontal=True)
df = lade_daten()

if menu == "🚀 Fahrt erfassen":
    fahrt_laeuft = False
    if not df.empty and (pd.isna(df.iloc[-1]["Endzeit"]) or str(df.iloc[-1]["Endzeit"]).strip() == ""):
        fahrt_laeuft = True
        aktuelle_fahrt = df.iloc[-1]

    if not fahrt_laeuft:
        st.subheader("Neue Fahrt starten")
        letzter_km = (
            float(df["KM_Ende"].dropna().iloc[-1])
            if not df.empty and not df["KM_Ende"].dropna().empty
            else 0.0
        )

        if "start_ort_text" not in st.session_state:
            st.session_state["start_ort_text"] = "Büro / Homeoffice"
        if "start_gps_coords" not in st.session_state:
            st.session_state["start_gps_coords"] = ""
        if "gps_start_aktiv" not in st.session_state:
            st.session_state["gps_start_aktiv"] = False

        if st.button("📍 GPS-Startort ermitteln", use_container_width=True):
            st.session_state["gps_start_aktiv"] = True

        if st.session_state["gps_start_aktiv"]:
            loc = get_geolocation(component_key="gps_start")
            if loc and "coords" in loc:
                lat = loc["coords"]["latitude"]
                lon = loc["coords"]["longitude"]
                st.session_state["start_ort_text"] = adresse_aus_gps(lat, lon)
                st.session_state["start_gps_coords"] = f"{lat},{lon}"
                st.session_state["gps_start_aktiv"] = False
                st.rerun()
            else:
                st.info("Start-Standort wird ermittelt... Bitte ggf. im Browser erlauben.")

        start_ort = st.text_input("Startort", key="start_ort_text")
        km_start = st.number_input("Tachostand Start (km):", min_value=0.0, step=1.0, value=letzter_km)

        if st.button("🚩 Fahrt Starten", type="primary", use_container_width=True):
            neue_zeile = pd.DataFrame([{
                "Datum": date.today().strftime("%Y-%m-%d"),
                "Startzeit": datetime.now().strftime("%H:%M"),
                "Endzeit": None,
                "Startort": str(start_ort),
                "Zielort": "",
                "KM_Start": float(km_start),
                "KM_Ende": None,
                "Gefahrene_KM": None,
                "Zweck": "",
                "Kategorie": "Dienstlich",
                "Start_GPS": st.session_state.get("start_gps_coords", "")
            }])
            df_neu = pd.concat([df, neue_zeile], ignore_index=True)
            try:
                conn.update(spreadsheet=SHEET_URL, worksheet="Tabellenblatt1", data=df_neu)
                st.session_state["reset_form"] = True
                st.rerun()
            except Exception as e:
                st.error(f"Schreibfehler: {e}")

    else:
        km_start_val = float(aktuelle_fahrt["KM_Start"])
        st.warning(
            f"Fahrt läuft seit **{aktuelle_fahrt['Startzeit']}** ab **{aktuelle_fahrt['Startort']}** "
            f"(Start: {km_start_val} km)"
        )

        if "ziel_ort_text" not in st.session_state:
            st.session_state["ziel_ort_text"] = ""
        if "gps_ziel_aktiv" not in st.session_state:
            st.session_state["gps_ziel_aktiv"] = False
        if "gps_berechnete_km" not in st.session_state:
            st.session_state["gps_berechnete_km"] = None

        if st.button("📍 GPS-Zielort & Strecke berechnen", use_container_width=True):
            st.session_state["gps_ziel_aktiv"] = True

        if st.session_state["gps_ziel_aktiv"]:
            loc = get_geolocation(component_key="gps_ziel")
            if loc and "coords" in loc:
                lat2 = loc["coords"]["latitude"]
                lon2 = loc["coords"]["longitude"]
                st.session_state["ziel_ort_text"] = adresse_aus_gps(lat2, lon2)

                start_gps_str = str(aktuelle_fahrt.get("Start_GPS", ""))
                if "," in start_gps_str and start_gps_str != "nan":
                    try:
                        lat1, lon1 = map(float, start_gps_str.split(","))
                        strecke_km = berechne_strassen_km(lat1, lon1, lat2, lon2)
                        if strecke_km is not None:
                            st.session_state["gps_berechnete_km"] = strecke_km
                            st.session_state["km_ende_input"] = round(km_start_val + strecke_km, 1)
                    except Exception:
                        pass

                st.session_state["gps_ziel_aktiv"] = False
                st.rerun()
            else:
                st.info("Zielort & Straßenstrecke werden ermittelt...")

        if st.session_state["gps_berechnete_km"] is not None:
            st.success(f"🛣️ Ermittelte GPS-Fahrstrecke: **{st.session_state['gps_berechnete_km']} km** (automatisch auf Start-Tacho addiert)")

        ziel_ort = st.text_input("Zielort / Kunde", key="ziel_ort_text", placeholder="z.B. Musterfirma GmbH")

        if "km_ende_input" not in st.session_state or st.session_state["km_ende_input"] < km_start_val:
            st.session_state["km_ende_input"] = km_start_val

        km_ende = st.number_input(
            "Tachostand Ankunft (km):",
            min_value=km_start_val,
            step=0.5,
            key="km_ende_input"
        )

        gefahrene_vorschau = round(km_ende - km_start_val, 1)
        st.caption(f"Gefahrene Strecke für diese Fahrt: **{gefahrene_vorschau} km**")

        kategorie = st.selectbox("Kategorie", ["Dienstlich", "Privat", "Arbeitsweg"])
        zweck = st.selectbox(
            "Zweck",
            ["Betriebsbegehung", "Gefährdungsbeurteilung", "Unterweisung", "ASA-Sitzung", "Sonstiges"]
        )
        notiz = st.text_input("Bemerkung (optional)")

        if st.button("🏁 Fahrt Stoppen & Speichern", type="primary", use_container_width=True):
            gefahrene_km = round(km_ende - km_start_val, 1)
            zweck_komplett = f"{zweck} ({notiz})" if notiz else zweck

            idx = df.index[-1]
            df.at[idx, "Endzeit"] = datetime.now().strftime("%H:%M")
            df.at[idx, "Zielort"] = str(ziel_ort)
            df.at[idx, "KM_Ende"] = float(km_ende)
            df.at[idx, "Gefahrene_KM"] = float(gefahrene_km)
            df.at[idx, "Zweck"] = str(zweck_komplett)
            df.at[idx, "Kategorie"] = str(kategorie)

            try:
                conn.update(spreadsheet=SHEET_URL, worksheet="Tabellenblatt1", data=df)
                st.session_state["reset_form"] = True
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

        anzeige_spalten = [c for c in df.columns if c != "Start_GPS"]
        st.dataframe(df[anzeige_spalten], use_container_width=True)

        csv_export = df[anzeige_spalten].to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button(
            "📥 Export als CSV",
            csv_export,
            "fahrtenbuch.csv",
            "text/csv",
            use_container_width=True
        )
    else:
        st.info("Noch keine Fahrten gespeichert.")
