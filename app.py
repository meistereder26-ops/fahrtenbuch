
  ⎿  Added 23 lines, removed 16 lines
      52  if menu == "➕ Neue Fahrt erfassen":
      53      st.header("Neue Fahrt eintragen")
      54
      55 +    # GPS-Hilfe per JavaScript / HTML Component (Browser Standort)
      56 +    st.markdown("""
      57 +    <div style="background-color: #f0f2f6; padding: 10px; border-radius: 8px; margin-bottom: 15px;">
      58 +        💡 <b>Tipp für unterwegs:</b> Wähle deine oft genutzten Stammstrecken aus oder nutze die Vorlag
         +en unten, um in Sekunden einzutragen.
      59 +    </div>
      60 +    """, unsafe_allow_html=True)
      61 +
      62      with st.form("fahrt_form"):
      63          col1, col2 = st.columns(2)
      64
      65          with col1:
      66              datum = st.date_input("Datum", value=date.today())
      60 -            fahrzeug = st.text_input("Fahrzeug / Kennzeichen", value="Firmierung / PKW 1")
      67 +            fahrzeug = st.text_input("Fahrzeug / Kennzeichen", value="Dienstwagen / PKW")
      68              kategorie = st.selectbox("Kategorie", ["Dienstlich", "Privat", "Wohnung - Arbeitsstätte"])
      69
      70          with col2:
     ...
      79              ]
      80              zweck_wahl = st.selectbox("Zweck-Vorlagen", zweck_optionen)
      81              zweck_custom = st.text_input("Zweck (Details)", value=zweck_wahl)
      75 -            kilometer = st.number_input("Gefahrene Kilometer (km)", min_value=0.1, step=0.5, value=15.0
         -)
      82
      83 +            # Kilometer mit Schnell-Tasten / Schieberegler oder Eingabe
      84 +            kilometer = st.number_input("Gefahrene Kilometer (km)", min_value=0.1, step=1.0, value=20.0
         +)
      85 +
      86          st.markdown("---")
      87          col3, col4 = st.columns(2)
      88          with col3:
      89              start = st.selectbox("Startort", options=favoriten, index=0)
      81 -            start_custom = st.text_input("Oder Startadresse manuell eingeben (optional)", value="")
      90 +            start_custom = st.text_input("Oder Startadresse manuell", value="")
      91          with col4:
      92              ziel = st.selectbox("Zielort", options=favoriten, index=min(1, len(favoriten)-1))
      84 -            ziel_custom = st.text_input("Oder Zieladresse manuell eingeben (optional)", value="")
      93 +            ziel_custom = st.text_input("Oder Zieladresse manuell", value="")
      94
      95          notiz = st.text_area("Notizen / Ansprechpartner vor Ort (optional)", placeholder="z.B. Begehung
           Halle 2 mit Herrn Müller")
      96
     ...
      101              final_ziel = ziel_custom if ziel_custom else ziel
      102
      103              neuer_eintrag = pd.DataFrame([{
       95 -                "ID": len(df) + 1,
      104 +                "ID": int(df['ID'].max()) + 1 if not df.empty and 'ID' in df.columns and pd.notna(df['
          +ID'].max()) else 1,
      105                  "Datum": datum,
      106                  "Fahrzeug": fahrzeug,
      107                  "Start": final_start,
     ...
      125      if df.empty:
      126          st.info("Noch keine Fahrten eingetragen.")
      127      else:
      119 -        # Filteroptionen
      128          col1, col2 = st.columns(2)
      129          with col1:
      130              filter_kat = st.multiselect("Nach Kategorie filtern", df['Kategorie'].unique(), default=df
           ['Kategorie'].unique())
     ...
      142
      143          st.dataframe(gefiltert, use_container_width=True)
      144
      137 -        # Eintrag löschen
      145          st.markdown("### Eintrag löschen")
      139 -        loesch_id = st.number_input("ID der Fahrt zum Löschen", min_value=1, max_value=int(df['ID'].ma
          -x()) if not df.empty else 1, step=1)
      140 -        if st.button("Ausgewählte Fahrt löschen 🗑️"):
      141 -            df = df[df['ID'] != loesch_id]
      142 -            speichere_daten(df)
      143 -            st.success(f"Fahrt mit ID {loesch_id} gelöscht!")
      144 -            st.rerun()
      146 +        if not df.empty:
      147 +            loesch_id = st.number_input("ID der Fahrt zum Löschen", min_value=int(df['ID'].min()), max
          +_value=int(df['ID'].max()), step=1)
      148 +            if st.button("Ausgewählte Fahrt löschen 🗑️"):
      149 +                df = df[df['ID'] != loesch_id]
      150 +                speichere_daten(df)
      151 +                st.success(f"Fahrt mit ID {loesch_id} gelöscht!")
      152 +                st.rerun()
      153
      154  # -------------------------------------------------------------
      155  # 3. FAVORITEN / ORTE
     ...
      170
      171      with col2:
      172          st.markdown("### Aktuelle Standorte:")
      165 -        for i, ort in enumerate(favoriten):
      173 +        for ort in favoriten:
      174              st.write(f"- {ort}")
      175
      176          ort_zu_loeschen = st.selectbox("Standort zum Löschen", options=favoriten)
     ...
      190      st.header("Auswertung & Finanzamt-Export")
      191
      192      if df.empty:
      185 -        st.info("Keine Daten für eine Auswertung vorhanden.")
      193 +        st.info("Noch keine Fahrten für eine Auswertung vorhanden.")
      194      else:
      195          col1, col2, col3 = st.columns(3)
      196
     ...
      208          st.markdown("---")
      209          st.subheader("Export für Buchhaltung / Finanzamt")
      210
      203 -        # CSV Export
      211          csv = df.to_csv(index=False).encode('utf-8')
      212          st.download_button(
      213              label="📥 Fahrtenbuch als CSV / Excel-kompatibel herunterladen",
