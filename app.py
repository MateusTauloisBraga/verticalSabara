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

        # Pré-processamento OpenCV
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

        # --- TEMPLATE MATCHING ---
        try:
            template = cv2.imread('template.png', 0)  # grayscale template
            if template is None:
                st.error("Template não encontrado. Verifique se 'template.png' está na pasta.")
                roi = gray
            else:
                res = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                threshold = 0.6
                if max_val >= threshold:
                    top_left = max_loc
                    h, w = template.shape
                    bottom_right = (top_left[0] + w, top_left[1] + h)

                    # Desenha retângulo para debug
                    img_display = img_cv.copy()
                    cv2.rectangle(img_display, top_left, bottom_right, (0, 255, 0), 2)
                    st.image(cv2.cvtColor(img_display, cv2.COLOR_BGR2RGB), caption="Template Matching detectado")

                    roi = gray[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
                else:
                    st.warning("Template não encontrado com confiança suficiente. Usando método por contornos.")
                    roi = None
        except Exception as e:
            st.error(f"Erro no template matching: {e}")
            roi = None

        # --- Fallback método contorno quadrado ---
        if roi is None:
            st.subheader("🔍 Pré-processamento com contornos (fallback)")

            gray_preview = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
            st.image(gray_preview, caption="Imagem em escala de cinza")

            # Reduz ruído e aplica binarização
            blur = cv2.medianBlur(gray, 3)
            thresh = cv2.adaptiveThreshold(
                blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 15, 4
            )
            thresh_preview = cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB)
            st.image(thresh_preview, caption="Imagem após blur + binarização")

            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            candidatos = []
            for c in contours:
                x, y, w, h = cv2.boundingRect(c)
                ratio = w / float(h)
                area = w * h
                if 0.7 <= ratio <= 1.3 and area > 100:
                    candidatos.append((c, area, x, y, w, h))

            if candidatos:
                c, area, x, y, w, h = max(candidatos, key=lambda item: item[1])
                roi = gray[y:y+h, x:x+w]

                roi_rgb = cv2.cvtColor(roi, cv2.COLOR_GRAY2RGB)
                st.image(roi_rgb, caption="🟩 ROI selecionada por contorno quadrado")
            else:
                roi = gray
                fallback_rgb = cv2.cvtColor(roi, cv2.COLOR_GRAY2RGB)
                st.image(fallback_rgb, caption="⚠️ ROI = imagem inteira (nenhum quadrado encontrado)")
                st.warning("Não foi detectada área quadrada. Usando imagem inteira para OCR.")


    # Mostrar tabela de resultados
    if st.session_state.registros:
        st.markdown("### 📋 Registros de Chegada")
        df = pd.DataFrame(st.session_state.registros)
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📁 Baixar resultados (.csv)",
            data=csv,
            file_name="resultados_cronometragem.csv",
            mime="text/csv"
        )
