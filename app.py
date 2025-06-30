import streamlit as st
from datetime import datetime
from PIL import Image
import pytesseract
import pandas as pd
import io
import numpy as np
import cv2

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

        # Abre imagem e exibe
        image = Image.open(img_file)
        st.image(image, caption="Imagem original")

        # Pré-processamento com OpenCV
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )

        # Mostra imagem binarizada
        st.image(thresh, caption="Imagem processada (binarizada)", channels="GRAY")

        # OCR com configuração customizada
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
        numero = pytesseract.image_to_string(thresh, config=custom_config).strip()

        st.text(f"OCR detectado: {numero if numero else '[vazio]'}")

        # Salva o registro se detectou número
        if numero:
            st.session_state.registros.append({
                'Número do Atleta': numero,
                'Hora de Chegada': chegada.strftime('%H:%M:%S'),
                'Tempo de Prova': str(tempo).split(".")[0]  # remove milissegundos
            })

            st.success(f"✅ Atleta **{numero}** registrado! Tempo: **{str(tempo).split('.')[0]}**")
        else:
            st.error("⚠️ Não foi possível identificar o número do atleta. Tente novamente com mais contraste ou melhor enquadramento.")

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
