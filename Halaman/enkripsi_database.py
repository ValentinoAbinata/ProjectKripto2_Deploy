import streamlit as st
import sqlite3
from Halaman.crypto_utils import encrypt_chacha20, decrypt_chacha20

def init_car_db():
    """Initialize database for cars dengan kolom baru"""
    conn = sqlite3.connect('cars.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT NOT NULL,
            brand TEXT NOT NULL,
            price TEXT NOT NULL,
            dekripsi_mobil TEXT  -- KOLOM BARU
        )
    ''')
    conn.commit()
    conn.close()

def create_car(model, brand, price, encryption_key):
    """Add new car to database dengan kolom dekripsi_mobil"""
    try:
        # Pastikan semua data adalah string sebelum dienkripsi
        model_str = str(model)
        brand_str = str(brand)
        price_str = str(price)
        
        # Encrypt all fields dengan kunci user
        encrypted_model = encrypt_chacha20(model_str, encryption_key)
        encrypted_brand = encrypt_chacha20(brand_str, encryption_key)
        encrypted_price = encrypt_chacha20(price_str, encryption_key)

        # KOLOM BARU: dekripsi_mobil - diisi dengan string kosong dulu
        encrypted_dekripsi = encrypt_chacha20("", encryption_key)

        if not all([encrypted_model, encrypted_brand, encrypted_price]):
            st.error("Gagal mengenkripsi data! Periksa kunci dan data input.")
            return False
            
        conn = sqlite3.connect('cars.db')
        c = conn.cursor()
        c.execute('INSERT INTO cars (model, brand, price, dekripsi_mobil) VALUES (?, ?, ?, ?)', 
                 (encrypted_model, encrypted_brand, encrypted_price, encrypted_dekripsi))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def read_cars(encryption_key):
    """Get all cars from database dengan kolom dekripsi_mobil"""
    try:
        conn = sqlite3.connect('cars.db')
        c = conn.cursor()
        c.execute('SELECT * FROM cars')
        encrypted_cars = c.fetchall()
        conn.close()
        
        successful_decrypts = 0
        total_cars = len(encrypted_cars)
        
        # Decrypt all fields dengan kunci user
        decrypted_cars = []
        for car in encrypted_cars:
            car_id, encrypted_model, encrypted_brand, encrypted_price, encrypted_dekripsi = car
            
            model = decrypt_chacha20(encrypted_model, encryption_key)
            brand = decrypt_chacha20(encrypted_brand, encryption_key)
            price = decrypt_chacha20(encrypted_price, encryption_key)
            dekripsi_mobil = decrypt_chacha20(encrypted_dekripsi, encryption_key)
            
            # Check if any field looks like wrong key
            has_errors = any(field.startswith('[') and field.endswith(']') for field in [model, brand, price, dekripsi_mobil])
            
            if not has_errors:
                successful_decrypts += 1
                try:
                    price_float = float(price)
                    decrypted_cars.append((car_id, model, brand, price_float, dekripsi_mobil, True))
                except ValueError:
                    decrypted_cars.append((car_id, model, brand, price, dekripsi_mobil, True))
            else:
                decrypted_cars.append((car_id, model, brand, price, dekripsi_mobil, False))
                
        return decrypted_cars, successful_decrypts, total_cars
        
    except Exception as e:
        st.error(f"Error membaca data mobil: {e}")
        return [], 0, 0
    
def update_car_dekripsi(car_data, dekripsi_text, encryption_key):
    """Update kolom dekripsi_mobil di database"""
    try:
        # Encrypt dekripsi_text dengan ChaCha20
        encrypted_dekripsi = encrypt_chacha20(dekripsi_text, encryption_key)
        
        conn = sqlite3.connect('cars.db')
        c = conn.cursor()
        
        # Cari mobil berdasarkan brand, model, price
        c.execute('''
            SELECT id FROM cars 
            WHERE brand = ? AND model = ? AND price = ?
        ''', (
            encrypt_chacha20(car_data['brand'], encryption_key),
            encrypt_chacha20(car_data['model'], encryption_key), 
            encrypt_chacha20(str(car_data['price']), encryption_key)
        ))
        
        result = c.fetchone()
        if result:
            car_id = result[0]
            # Update kolom dekripsi_mobil
            c.execute('''
                UPDATE cars SET dekripsi_mobil = ? WHERE id = ?
            ''', (encrypted_dekripsi, car_id))
            conn.commit()
            conn.close()
            return True
        else:
            conn.close()
            return False
            
    except Exception as e:
        st.error(f"Error update deskripsi: {e}")
        return False
    
def delete_car(car_id):
    """Delete car from database"""
    try:
        conn = sqlite3.connect('cars.db')
        c = conn.cursor()
        c.execute('DELETE FROM cars WHERE id = ?', (car_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

# ===== PAGE =====
def page_car_database():
    st.header("🚗 Database Mobil dengan Enkripsi ChaCha20") 
    
    # Initialize car database
    init_car_db()
    
    # Input kunci enkripsi dari user
    st.subheader("🔑 Kunci Enkripsi")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        encryption_key = st.text_input(
            "Masukkan Kunci Enkripsi:", 
            type="password",
            placeholder="Kunci yang sama harus digunakan untuk encrypt dan decrypt",
            help="Coba kunci berbeda untuk melihat efeknya pada data terdekripsi!"
        )
    
    with col2:
        show_encrypted = st.checkbox("Tampilkan Data Terenkripsi", help="Lihat data asli di database")
    
    if not encryption_key:
        st.warning("⚠️ Silakan masukkan kunci enkripsi untuk mengakses database mobil.")
        st.info("""
        **Fitur Baru:**
        - Data akan tetap ditampilkan meski kunci salah
        - Anda bisa melihat bagaimana kunci yang berbeda menghasilkan data terdekripsi yang berbeda
        - Kunci yang benar akan menampilkan data yang bermakna
        """)
        
        # Tampilkan data terenkripsi saja jika checkbox dicentang
        if show_encrypted:
            display_encrypted_data_only()
        return
    
    # Info tentang status kunci
    with st.expander("ℹ️ Status Kunci & Enkripsi"):
        st.write(f"""
        **Kunci Saat Ini:** `{encryption_key[:8]}...` (panjang: {len(encryption_key)} karakter)
        
        **Cara Kerja:**
        - Setiap kunci akan menghasilkan output dekripsi yang berbeda
        - Hanya kunci yang benar yang akan menampilkan data asli
        - Kunci salah akan menampilkan karakter acak atau pesan error
        """)
        

    tab1, tab2 = st.tabs(["➕ Tambah Mobil", "📋 Lihat & Hapus Mobil"])
    
    with tab1:
        st.subheader("Tambah Mobil Baru (Terenkripsi)")
        
        with st.form("add_car_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                brand = st.text_input("Brand Mobil", placeholder="Contoh: Toyota, Honda, dll.")
                model = st.text_input("Model Mobil", placeholder="Contoh: Camry, Civic, dll.")
            
            with col2:
                price = st.number_input("Harga Mobil (Rp)", min_value=0, step=1000000, 
                                    format="%d", value=100000000)
            
            submit_button = st.form_submit_button("💾 Simpan Mobil (Terenkripsi)")
            
            if submit_button:
                if not brand or not model:
                    st.error("Brand dan Model harus diisi!")
                elif price <= 0:
                    st.error("Harga harus lebih dari 0!")
                else:
                    if create_car(model, brand, price, encryption_key):
                        st.success(f"✅ Mobil {brand} {model} berhasil ditambahkan dengan enkripsi!")
                        
                        # AUTO REDIRECT KE SUPER ENCRYPTION
                        st.session_state.current_page = "Super Encryption"
                        st.session_state.new_car_data = {
                            'brand': brand,
                            'model': model, 
                            'price': price,
                            'encryption_key': encryption_key
                        }
                        st.rerun()
                    else:
                        st.error("❌ Gagal menambahkan mobil!")
    
    with tab2:
        st.subheader("Daftar Mobil (Hasil Dekripsi)")
        
        cars, successful_decrypts, total_cars = read_cars(encryption_key)
        
        if total_cars > 0:
            if successful_decrypts == total_cars:
                st.success(f"✅ Semua {total_cars} mobil berhasil didekripsi dengan kunci ini!")
            elif successful_decrypts > 0:
                st.warning(f"⚠️ {successful_decrypts} dari {total_cars} mobil berhasil didekripsi.")
            else:
                st.error(f"❌ Tidak ada data yang berhasil didekripsi dengan kunci ini.")
        
        if not cars:
            st.info("📝 Belum ada data mobil.")
        else:
            st.write(f"**Menampilkan {len(cars)} mobil:**")
            
            for car in cars:
                car_id, model, brand, price, dekripsi_mobil, decrypt_success = car
                
                with st.container():
                    if decrypt_success:
                        st.markdown(f'<div style="border-left: 4px solid #00ff00; padding-left: 10px;">', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div style="border-left: 4px solid #ff0000; padding-left: 10px;">', unsafe_allow_html=True)
                    
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                    
                    with col1:
                        if decrypt_success:
                            st.write(f"**{brand} {model}**")
                        else:
                            st.write(f"~~{brand} {model}~~")
                        st.caption(f"ID: {car_id}")
                    
                    with col2:
                        if isinstance(price, (int, float)):
                            st.write(f"**Harga:** Rp {price:,.0f}")
                        else:
                            st.write(f"**Harga:** {price}")
                    
                    with col3:
                        st.write("**Dekripsi Mobil:**")
                        if dekripsi_mobil and dekripsi_mobil != "[EMPTY]":
                            st.code(dekripsi_mobil[:50] + "..." if len(dekripsi_mobil) > 50 else dekripsi_mobil)
                        else:
                            st.info("Belum diisi")
                    
                    with col4:
                        if st.button(f"🗑️", key=f"delete_{car_id}"):
                            if delete_car(car_id):
                                st.success("✅ Data dihapus!")
                                st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.divider()

def display_encrypted_data():
    """Display raw encrypted data from database"""
    st.subheader("🔐 Data Terenkripsi di Database")
    
    try:
        conn = sqlite3.connect('cars.db')
        c = conn.cursor()
        c.execute('SELECT * FROM cars')
        encrypted_cars = c.fetchall()
        conn.close()
        
        if not encrypted_cars:
            st.info("Tidak ada data terenkripsi di database.")
            return
            
        for car in encrypted_cars:
            car_id, encrypted_model, encrypted_brand, encrypted_price = car
            
            with st.expander(f"Data Terenkripsi - Mobil ID {car_id}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Model:**")
                    st.code(encrypted_model)
                    st.write(f"Panjang: {len(encrypted_model)} karakter")
                
                with col2:
                    st.write("**Brand:**")
                    st.code(encrypted_brand)
                    st.write(f"Panjang: {len(encrypted_brand)} karakter")
                
                st.write("**Harga:**")
                st.code(encrypted_price)
                st.write(f"Panjang: {len(encrypted_price)} karakter")
                
    except Exception as e:
        st.error(f"Error mengambil data terenkripsi: {e}")

def display_encrypted_data_only():
    """Display only encrypted data when no key is provided"""
    st.subheader("🔐 Data Terenkripsi di Database")
    st.info("Masukkan kunci untuk mencoba mendekripsi data berikut:")
    
    display_encrypted_data()
