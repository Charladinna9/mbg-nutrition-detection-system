import streamlit as st
from auth import login_user, register_user
from db import get_connection
import pandas as pd
from PIL import Image
from ultralytics import YOLO

def get_gizi(nama_makanan):

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM tkpi WHERE nama_makanan=%s",
        (nama_makanan,)
    )

    data = cursor.fetchone()

    cursor.close()
    conn.close()

    return data

def simpan_hasil(
    user_id,
    foto,
    energi,
    protein,
    lemak,
    karbo,
    serat
):

    conn = get_connection()

    cursor = conn.cursor()

    sql = """
    INSERT INTO hasil_deteksi
    (
        user_id,
        foto,
        energi_total,
        protein_total,
        lemak_total,
        karbo_total,
        serat_total
    )
    VALUES
    (%s,%s,%s,%s,%s,%s,%s)
    """

    cursor.execute(
        sql,
        (
            user_id,
            foto,
            energi,
            protein,
            lemak,
            karbo,
            serat
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

st.set_page_config(page_title="MBG Nutrition", layout="centered", page_icon="🍲")

# Session State
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# ====================== LOGIN ======================
if not st.session_state.logged_in:
    st.title("🔐 Login MBG Nutrition System")
    st.markdown("### Program Deteksi Gizi Makanan MBG")

    menu_auth = st.radio(
        "Pilih Menu",
        ["Login", "Register"]
    )

    if menu_auth == "Login":

        username = st.text_input("Username")
        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button("Login"):

            user = login_user(
                username,
                password
            )

            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.rerun()

            else:
                st.error("Username atau password salah")

    elif menu_auth == "Register":

        nama = st.text_input("Nama Lengkap")
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button("Daftar"):

            sukses = register_user(
                username=username,
                email=email,
                password=password,
                role="user",
                nama_lengkap=nama
            )

            if sukses:
                st.success(
                    "Registrasi berhasil"
                )

            else:
                st.error(
                    "Registrasi gagal"
                )
else:
    # Sudah Login
    user = st.session_state.user
    st.sidebar.success(f"👤 {user['nama_lengkap']}")
    st.sidebar.caption(f"Role: **{user['role'].upper()}**")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

    # Menu
    if user['role'] == 'admin':
       menu = st.sidebar.radio(
            "Menu",
            ["Deteksi Makanan", "Laporan", "Kelola TKPI"]
    )
    else:
        menu = st.sidebar.radio("Menu", ["Deteksi Makanan", "Riwayat Saya"])

    # ==================== HALAMAN DETEKSI ====================
    if menu == "Deteksi Makanan":

        st.title("🍲 Deteksi Program Gizi MBG - YOLOv11")
        st.subheader("Upload foto piring makanan")

        uploaded_file = st.file_uploader(
            "Pilih Foto",
            type=["jpg", "jpeg", "png"]
        )

        if uploaded_file:

            image = Image.open(uploaded_file)

            col1, col2 = st.columns(2)
            with col1:
                st.image(
                    image,
                    caption="Foto yang diupload",
                    use_container_width=280
              )

            model = YOLO("models/best.pt")

            results = model(
                image,
                conf=0.5
            )

            annotated = results[0].plot()

            with col2:
                st.image(
                    annotated,
                    caption="Hasil Deteksi YOLO",
                    use_container_width=280
                )

            st.success("✅ Deteksi selesai!")

            st.subheader("🍽️ Makanan Terdeteksi")

            detected_foods = []

            for box in results[0].boxes:

                class_id = int(box.cls[0])

                nama_makanan = model.names[class_id]

                detected_foods.append(nama_makanan)

            detected_foods = list(set(detected_foods))

            if len(detected_foods) == 0:

                st.warning("Tidak ada makanan terdeteksi")

            else:

                for makanan in detected_foods:
                    st.write(f"✅ {makanan}")
                

            # ========================
            # ESTIMASI NILAI GIZI
            # ========================

            st.subheader("🥗 Estimasi Nilai Gizi")

            total_energi = 0
            total_protein = 0
            total_lemak = 0
            total_karbo = 0
            total_serat = 0

            detail_gizi = []

            for makanan in detected_foods:

                data = get_gizi(makanan)

                if data:

                    detail_gizi.append({
                        "Makanan": makanan,
                        "Energi": data["energi"],
                        "Protein": data["protein"],
                        "Lemak": data["lemak"],
                        "Karbohidrat": data["karbohidrat"],
                        "Serat": data["serat"]
                    })

                    total_energi += data["energi"]
                    total_protein += data["protein"]
                    total_lemak += data["lemak"]
                    total_karbo += data["karbohidrat"]
                    total_serat += data["serat"]
                   
            st.subheader("📋 Detail Gizi per Makanan")

            df_gizi = pd.DataFrame(detail_gizi)

            st.dataframe(
                df_gizi,
                width=600,
                height=220
            )
                            
            st.success("Total Gizi")
            st.write(f"Energi : {total_energi:.1f} kkal")
            st.write(f"Protein : {total_protein:.1f} g")
            st.write(f"Lemak : {total_lemak:.1f} g")
            st.write(f"Karbohidrat : {total_karbo:.1f} g")
            st.write(f"Serat : {total_serat:.1f} g")
         
            if st.button("💾 Simpan Hasil"):

                simpan_hasil(
                    user["id"],
                    uploaded_file.name,
                    total_energi,
                    total_protein,
                    total_lemak,
                    total_karbo,
                    total_serat
                )

                st.success("Data berhasil disimpan")

                st.balloons()

            # ==================== HALAMAN LAPORAN ====================
    if menu == "Laporan":

        st.title("📊 Laporan Deteksi")

        conn = get_connection()

        query = """
        SELECT *
        FROM hasil_deteksi
        ORDER BY id DESC
        """

        df = pd.read_sql(query, conn)

        conn.close()

        st.dataframe(
            df,
            width=800,
            height=300
        )

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="laporan_deteksi.csv",
            mime="text/csv"
        )

        if len(df) > 0:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📈 Grafik Energi")
                st.bar_chart(df["energi_total"])

            with col2:
                st.subheader("💪 Grafik Protein")
                st.bar_chart(df["protein_total"])

            col3, col4 = st.columns(2)

            with col3:
                st.subheader("🍚 Grafik Karbohidrat")
                st.bar_chart(df["karbo_total"])

            with col4:
                st.subheader("🥑 Grafik Lemak")
                st.bar_chart(df["lemak_total"])

            col5, col6 = st.columns(2)   
            with col5:
                st.subheader("🌾 Grafik Serat")
                st.bar_chart(df["serat_total"])

            with col6:
                st.empty()
                
            st.subheader("📋 Ringkasan Laporan")

            st.metric(
                "Rata-rata Energi",
                f"{df['energi_total'].mean():.1f} kkal"
            )

            st.metric(
                "Rata-rata Protein",
                f"{df['protein_total'].mean():.1f} g"
            )

            st.metric(
                "Jumlah Deteksi",
                len(df)
            )

            st.metric(
                "Rata-rata Karbohidrat",
                f"{df['karbo_total'].mean():.1f} g"
            )

            st.divider()

            st.caption(
                "Sistem Estimasi Nilai Gizi Program Makan Bergizi Gratis (MBG) Menggunakan YOLOv11 dan TKPI"
            )


        else:
            st.warning("Belum ada data laporan")

    if menu == "Kelola TKPI":

                st.title("📚 Kelola Data TKPI")

                conn = get_connection()

                df = pd.read_sql(
                    "SELECT * FROM tkpi",
                    conn
                )

                st.dataframe(
                    df,
                    width=800,
                    height=300
                )

                # =========================
                # TAMBAH DATA
                # =========================
                st.subheader("➕ Tambah Data")

                nama = st.text_input("Nama Makanan")
                berat = st.number_input("Berat Porsi")
                energi = st.number_input("Energi")
                protein = st.number_input("Protein")
                lemak = st.number_input("Lemak")
                karbo = st.number_input("Karbohidrat")
                serat = st.number_input("Serat")

                if st.button("Tambah"):

                    cursor = conn.cursor()

                    cursor.execute(
                        """
                        INSERT INTO tkpi
                        (
                            nama_makanan,
                            berat_porsi,
                            energi,
                            protein,
                            lemak,
                            karbohidrat,
                            serat
                        )
                        VALUES
                        (%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            nama,
                            berat,
                            energi,
                            protein,
                            lemak,
                            karbo,
                            serat
                        )
                    )

                    conn.commit()
                    cursor.close()
                    st.success("Data berhasil ditambahkan")
                    st.rerun()

                # =========================
                # EDIT DATA
                # =========================
                st.subheader("✏️ Edit Data TKPI")

                edit_id = st.number_input(
                    "ID Data yang akan diubah",
                    min_value=1,
                    step=1,
                    key="edit_id"
                )

                edit_nama = st.text_input(
                    "Nama Makanan Baru",
                    key="edit_nama"
                )

                edit_berat = st.number_input(
                    "Berat Porsi Baru",
                    key="edit_berat"
                )

                edit_energi = st.number_input(
                    "Energi Baru",
                    key="edit_energi"
                )

                edit_protein = st.number_input(
                    "Protein Baru",
                    key="edit_protein"
                )

                edit_lemak = st.number_input(
                    "Lemak Baru",
                    key="edit_lemak"
                )

                edit_karbo = st.number_input(
                    "Karbohidrat Baru",
                    key="edit_karbo"
                )

                edit_serat = st.number_input(
                    "Serat Baru",
                    key="edit_serat"
                )

                if st.button("Update Data"):

                    cursor = conn.cursor()

                    cursor.execute(
                        """
                        UPDATE tkpi
                        SET
                            nama_makanan=%s,
                            berat_porsi=%s,
                            energi=%s,
                            protein=%s,
                            lemak=%s,
                            karbohidrat=%s,
                            serat=%s
                        WHERE id=%s
                        """,
                        (
                            edit_nama,
                            edit_berat,
                            edit_energi,
                            edit_protein,
                            edit_lemak,
                            edit_karbo,
                            edit_serat,
                            edit_id
                        )
                    )

                    conn.commit()
                    cursor.close()
                    st.success("Data berhasil diubah")
                    st.rerun()

                # =========================
                # HAPUS DATA
                # =========================
                st.subheader("🗑️ Hapus Data")

                hapus_id = st.number_input(
                    "ID Data",
                    min_value=1,
                    step=1,
                    key="hapus_id"
                )

                if st.button("Hapus"):

                    cursor = conn.cursor()

                    cursor.execute(
                        "DELETE FROM tkpi WHERE id=%s",
                        (hapus_id,)
                    )

                    conn.commit()
                    cursor.close()
                    
                    st.success("Data berhasil dihapus")
                    st.rerun()

                conn.close()


    if menu == "Riwayat Saya":

                    st.title("📋 Riwayat Deteksi Saya")

                    conn = get_connection()

                    query = """
                    SELECT *
                    FROM hasil_deteksi
                    WHERE user_id = %s
                    ORDER BY id DESC
                    """

                    df = pd.read_sql(
                        query,
                        conn,
                        params=(user["id"],)
                    )

                    conn.close()

                    if len(df) == 0:

                        st.info("Belum ada riwayat deteksi")

                    else:

                        st.dataframe(
                            df,
                            width=800,
                            height=300
                        )

                        csv = df.to_csv(index=False).encode("utf-8")

                        st.download_button(
                            "📥 Download Riwayat",
                            csv,
                            "riwayat_saya.csv",
                            "text/csv"
                        )

                        st.metric(
                            "Jumlah Riwayat",
                            len(df)
                        )
                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("📈 Grafik Energi")
                        st.bar_chart(df["energi_total"])
                    with col2:
                        st.subheader("💪 Grafik Protein")
                        st.bar_chart(df["protein_total"])

                    col3, col4 = st.columns(2)  

                    with col3:
                        st.subheader("🍚 Grafik Karbohidrat")
                        st.bar_chart(df["karbo_total"])

                    with col4:
                        st.subheader("🥑 Grafik Lemak")
                        st.bar_chart(df["lemak_total"])

                    col5, col6 = st.columns(2) 

                    with col5:
                        st.subheader("🌾 Grafik Serat")
                        st.bar_chart(df["serat_total"])

                    with col6:
                        st.empty()
                        
                        st.subheader("📋 Ringkasan")

                        st.metric(
                            "Rata-rata Energi",
                            f"{df['energi_total'].mean():.1f} kkal"
                        )

                        st.metric(
                            "Rata-rata Protein",
                            f"{df['protein_total'].mean():.1f} g"
                        )

                        st.metric(
                            "Jumlah Deteksi",
                            len(df)
                        )

                        st.metric(
                            "Rata-rata Karbohidrat",
                            f"{df['karbo_total'].mean():.1f} g"
                        )

                        st.caption(
                            "Sistem Estimasi Nilai Gizi Program Makan Bergizi Gratis (MBG) Menggunakan YOLOv11 dan TKPI"
                        )


                        