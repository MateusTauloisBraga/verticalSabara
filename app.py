import streamlit as st
from datetime import datetime
from PIL import Image
import pytesseract
import pandas as pd
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

    st.markdown("### 📸 Captura ou upload de imagem do atleta")
    img_file = st.camera_input("📷 Tire uma foto do atleta") or st.file_uploader("⬆️ Ou envie uma imagem", type=["png", "jpg", "jpeg"])

    if img_file is not None:
        chegada = datetime.now()
        tempo = chegada - st.session_state.start_time

        image = Image.open(img_file).convert("RGB")
        st.image(image, caption="Imagem original")

        # Pré-processamento com OpenCV
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

        # Reduz ruído e aumenta contraste
        blur = cv2.medianBlur(gray, 3)
        thresh = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 15, 4
        )

        st.image(thresh, caption="Imagem binarizada", channels="GRAY")

        # Detecta contornos
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filtra contornos aproximados a quadrados (razão largura/altura ~ 1)
        candidatos = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            ratio = w / float(h)
            area = w * h
            if 0.7 <= ratio <= 1.3 and area > 100:  # area mínima para evitar ruído
                candidatos.append((c, area, x, y, w, h))

        if candidatos:
            # Pega o maior candidato
            c, area, x, y, w, h = max(candidatos, key=lambda item: item[1])
            roi = gray[y:y+h, x:x+w]
            st.image(roi, caption="Área detectada com contorno aproximadamente quadrado (ROI)", channels="GRAY")
        else:
            roi = gray
            st.warning("Não foi detectada área quadrada. Usando imagem inteira para OCR.")

        # OCR com configuração customizada
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
        numero = pytesseract.image_to_string(roi, config=custom_config).strip()
        st.text(f"OCR detectado: {numero if numero else '[vazio]'}")

        if numero:
            st.session_state.registros.append({
                'Número do Atleta': numero,
                'Hora de Chegada': chegada.strftime('%H:%M:%S'),
                'Tempo de Prova': str(tempo).split(".")[0]
            })

            st.success(f"✅ Atleta **{numero}** registrado! Tempo: **{str(tempo).split('.')[0]}**")
        else:
            st.error("⚠️ Não foi possível identificar o número do atleta. Tente outra imagem ou maior contraste.")

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
