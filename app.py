import streamlit as st
from datetime import datetime
from PIL import Image
import pytesseract
import pandas as pd
import io

st.set_page_config(page_title="Cronometragem Vertical", layout="centered")
st.title("📸 Cronometragem de Prova Vertical")

# Inicializa variáveis na sessão
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
    st.session_state.registros = []

# Botão para iniciar a cronometragem
if st.button("🟢 Iniciar Prova"):
    st.session_state.start_time = datetime.now()
    st.success(f"Largada iniciada às {st.session_state.start_time.strftime('%H:%M:%S')}")

# Mostra o horário da largada
if st.session_state.start_time:
    st.markdown(f"**⏱️ Largada:** {st.session_state.start_time.strftime('%H:%M:%S')}")

    # Captura de imagem do atleta
    img_file = st.camera_input("📷 Tire uma foto do atleta na chegada")

    if img_file is not None:
        chegada = datetime.now()
        tempo = chegada - st.session_state.start_time

        image = Image.open(img_file)

        # OCR para extrair número do atleta
        numero = pytesseract.image_to_string(image, config='--psm 6 digits')
        numero = numero.strip()

        # Salva o registro
        st.session_state.registros.append({
            'Número do Atleta': numero,
            'Hora de Chegada': chegada.strftime('%H:%M:%S'),
            'Tempo de Prova': str(tempo).split(".")[0]  # remove milissegundos
        })

        st.success(f"✅ Atleta **{numero}** registrado! Tempo: **{str(tempo).split('.')[0]}**")

    # Mostrar tabela de resultados
    if st.session_state.registros:
        st.markdown("### 📋 Registros de Chegada")
        df = pd.DataFrame(st.session_state.registros)
        st.dataframe(df, use_container_width=True)

        # Botão para exportar CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📁 Baixar resultados (.csv)",
            data=csv,
            file_name="resultados_cronometragem.csv",
            mime="text/csv"
        )
