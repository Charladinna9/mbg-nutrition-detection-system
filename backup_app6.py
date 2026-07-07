# ========================
# IMPORT
# ========================
import streamlit as st
from PIL import Image
import numpy as np
from tensorflow.keras.models import load_model
from roboflow import Roboflow
import tempfile
import pandas as pd

# ========================
# LOGIN ADMIN
# ========================

ADMIN_USER = "admin"
ADMIN_PASS = "123"

if "login" not in st.session_state:
    st.session_state.login = False

# ========================
# HALAMAN LOGIN
# ========================

if not st.session_state.login:

    st.title("🔐 Login Admin")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if username == ADMIN_USER and password == ADMIN_PASS:

            st.session_state.login = True

            st.rerun()

        else:
            st.error("Username atau password salah")

# ========================
# HALAMAN APLIKASI
# ========================

if st.session_state.login:

    # ========================
    # TITLE
    # ========================
    st.title("🍽️ Deteksi Makanan & Estimasi Nilai Gizi")

    # tombol logout
    if st.button("Logout"):
        st.session_state.login = False
        st.rerun()

    # ========================
    # LOAD MODEL CNN
    # ========================
    model = load_model("model_gizi.keras")

    # ========================
    # ROBOFLOW SETUP
    # ========================
    rf = Roboflow(api_key="zMtBFlolNl3p5dQtFFB3")
    project = rf.workspace("charladinna-bbx").project("deteksi-mbg")
    

    # versi model roboflow
    version = project.version(1)

    model_rf = version.model

    # ========================
    # MAPPING NAMA CLASS
    # ========================
    mapping = {

        "nasi putih": "nasi",
        "mie goreng": "mie",
        "ayam goreng": "ayam",
        "sayur bayam": "sayur",
        "tempe goreng": "tempe",
        "tahu goreng": "tahu",
        "jeruk": "buah",
        "orange": "buah",
        "keju slice": "keju",
        "cheese": "keju"
    }

    # ========================
    # DATABASE GIZI
    # ========================
    gizi_db = {

        "ayam": {
            "energi": 239,
            "protein": 27,
            "lemak": 14,
            "karbo": 0,
            "serat": 0
        },

        "bakso": {
            "energi": 160,
            "protein": 9,
            "lemak": 11,
            "karbo": 5,
            "serat": 0
        },

        "buah": {
            "energi": 60,
            "protein": 0.5,
            "lemak": 0.2,
            "karbo": 15,
            "serat": 2
        },

        "kacang": {
            "energi": 567,
            "protein": 26,
            "lemak": 49,
            "karbo": 16,
            "serat": 9
        },

        "keju": {
            "energi": 402,
            "protein": 25,
            "lemak": 33,
            "karbo": 1.3,
            "serat": 0
        },

        "kentang": {
            "energi": 77,
            "protein": 2,
            "lemak": 0.1,
            "karbo": 17,
            "serat": 2.2
        },

        "mie": {
            "energi": 138,
            "protein": 5,
            "lemak": 2,
            "karbo": 25,
            "serat": 1
        },

        "nasi": {
            "energi": 175,
            "protein": 3,
            "lemak": 0.3,
            "karbo": 40,
            "serat": 0.4
        },

        "roti": {
            "energi": 265,
            "protein": 9,
            "lemak": 3.2,
            "karbo": 49,
            "serat": 2.7
        },

        "sayur": {
            "energi": 50,
            "protein": 2,
            "lemak": 0.2,
            "karbo": 10,
            "serat": 3
        },

        "susu": {
            "energi": 61,
            "protein": 3.2,
            "lemak": 3.3,
            "karbo": 5,
            "serat": 0
        },

        "tahu": {
            "energi": 76,
            "protein": 8,
            "lemak": 4.8,
            "karbo": 1.9,
            "serat": 0.3
        },

        "telur": {
            "energi": 155,
            "protein": 13,
            "lemak": 11,
            "karbo": 1.1,
            "serat": 0
        },

        "tempe": {
            "energi": 193,
            "protein": 20,
            "lemak": 11,
            "karbo": 9,
            "serat": 1.4
        }
    }

    # ========================
    # FUNGSI DETEKSI
    # ========================
    def detect_food(image_path):

        try:

            result = model_rf.predict(
                image_path,
                confidence=20,
                overlap=30
            ).json()

            detected = []

            if "predictions" in result:

                for item in result["predictions"]:

                    nama = item["class"]

                    # mapping class
                    if nama in mapping:
                        nama = mapping[nama]

                    detected.append(nama)

            return list(set(detected)), result

        except Exception as e:

            st.error(f"Error Roboflow: {e}")

            return [], {}

    # ========================
    # UPLOAD GAMBAR
    # ========================
    uploaded_file = st.file_uploader(
        "Upload gambar makanan",
        type=["jpg", "jpeg", "png"]
    )

    # ========================
    # PROSES
    # ========================
    if uploaded_file is not None:

        # buka gambar
        image = Image.open(
            uploaded_file
        ).convert("RGB")

        # tampilkan gambar
        st.image(
            image,
            caption="Gambar Upload",
            width=500
        )

        # simpan sementara
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".jpg"
        ) as tmp:

            image.save(tmp.name)

            img_path = tmp.name

        # ========================
        # DETEKSI MAKANAN
        # ========================
        detected_items, raw_result = detect_food(
            img_path
        )

        # ========================
        # DEBUG ROBOFLOW
        # ========================
        st.subheader("🔍 Debug Roboflow")

        st.write(raw_result)

        # ========================
        # HASIL DETEKSI
        # ========================
        st.subheader("🍽️ Makanan Terdeteksi")

        if len(detected_items) == 0:

            st.warning(
                "Tidak ada makanan terdeteksi"
            )

        else:

            for item in detected_items:

                st.write(f"- {item}")

        # ========================
        # HITUNG GIZI
        # ========================
        total = {
            "energi": 0,
            "protein": 0,
            "lemak": 0,
            "karbo": 0,
            "serat": 0
        }

        for item in detected_items:

            if item in gizi_db:

                for key in total:

                    total[key] += gizi_db[item][key]

        # ========================
        # OUTPUT GIZI
        # ========================
        st.subheader("🥗 Estimasi Nilai Gizi")

        st.write(
            f"Energi : {total['energi']} kkal"
        )

        st.write(
            f"Protein : {total['protein']} g"
        )

        st.write(
            f"Lemak : {total['lemak']} g"
        )

        st.write(
            f"Karbohidrat : {total['karbo']} g"
        )

        st.write(
            f"Serat : {total['serat']} g"
        )

        # ========================
        # PREDIKSI CNN
        # ========================
        img = image.resize((224, 224))

        img = np.array(img) / 255.0

        img = np.expand_dims(
            img,
            axis=0
        )

        prediction = model.predict(img)

        gizi_total_cnn = float(
            prediction[0][0]
        )

        # ========================
        # OUTPUT CNN
        # ========================
        st.subheader("📊 Output CNN")

        st.metric(
            "Nilai Gizi Total",
            f"{gizi_total_cnn:.2f}"
        )

        st.success("Prediksi selesai 🚀")

        # ========================
        # TABEL HASIL
        # ========================
        hasil_df = pd.DataFrame({

            "Komponen": [
                "Energi",
                "Protein",
                "Lemak",
                "Karbohidrat",
                "Serat"
            ],

            "Nilai": [
                total["energi"],
                total["protein"],
                total["lemak"],
                total["karbo"],
                total["serat"]
            ]
        })

        # tampilkan tabel
        st.subheader("📋 Tabel Hasil Gizi")

        st.dataframe(hasil_df)

        # ========================
        # CONVERT CSV
        # ========================
        csv = hasil_df.to_csv(
            index=False
        ).encode("utf-8")

        # ========================
        # DOWNLOAD BUTTON
        # ========================
        st.download_button(
            label="⬇️ Unduh Hasil CSV",
            data=csv,
            file_name="hasil_gizi.csv",
            mime="text/csv"
        )