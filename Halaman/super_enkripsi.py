import streamlit as st
import base64
from Halaman.enkripsi_database import update_car_dekripsi

def caesar_cipher(text, shift):
    result = ""
    for char in str(text):
        if char.isalpha():
            ascii_offset = 65 if char.isupper() else 97
            shifted_char = chr((ord(char) - ascii_offset + shift) % 26 + ascii_offset)
            result += shifted_char
        elif char.isdigit():
            shifted_digit = str((int(char) + shift) % 10)
            result += shifted_digit
        else:
            result += char
    return result

def xor_encrypt_base64(text, key):
    result_bytes = bytearray()
    ascii_values = []
    key_length = len(key)
    
    # Enkripsi setiap karakter dengan XOR
    for i, char in enumerate(str(text)):
        key_char = key[i % key_length]
        xor_result = ord(char) ^ ord(key_char)
        
        result_bytes.append(xor_result)
        ascii_values.append(xor_result)
    
    # Convert ke Base64 untuk memastikan semua karakter printable
    result_base64 = base64.b64encode(result_bytes).decode('utf-8')
    return result_base64, ascii_values

def xor_decrypt_base64(encrypted_base64, key):
    """Decrypt XOR dari Base64"""
    try:
        # Decode dari Base64 kembali ke bytes
        encrypted_bytes = base64.b64decode(encrypted_base64)
        
        result = ""
        ascii_values = []
        key_length = len(key)
        
        # Dekripsi setiap byte
        for i, byte_val in enumerate(encrypted_bytes):
            key_char = key[i % key_length]
            xor_result = byte_val ^ ord(key_char)
            result += chr(xor_result)
            ascii_values.append(xor_result)
            
        return result, ascii_values
    except Exception as e:
        # Fallback untuk data yang bukan Base64 (kompatibilitas dengan data lama)
        return xor_decrypt_fallback(encrypted_base64, key)

def xor_decrypt_fallback(encrypted_text, key):
    """Fallback decrypt untuk data lama yang belum pakai Base64"""
    result = ""
    ascii_values = []
    key_length = len(key)
    
    for i, char in enumerate(encrypted_text):
        key_char = key[i % key_length]
        xor_result = ord(char) ^ ord(key_char)
        result += chr(xor_result)
        ascii_values.append(xor_result)
        
    return result, ascii_values

def super_encrypt(text, caesar_key, xor_key):
    """Super encrypt dengan Base64 XOR"""
    # Step 1: Caesar Cipher
    caesar_result = caesar_cipher(text, caesar_key)
    
    # Step 2: XOR dengan Base64 encoding
    final_result, ascii_values = xor_encrypt_base64(caesar_result, xor_key)
    
    return caesar_result, final_result, ascii_values

def super_decrypt(encrypted_text, caesar_key, xor_key):
    """Super decrypt dengan Base64 XOR"""
    # Step 1: XOR decrypt (auto-detect Base64 atau legacy)
    xor_result, ascii_values = xor_decrypt_base64(encrypted_text, xor_key)
    
    # Step 2: Caesar decrypt
    final_result = caesar_cipher(xor_result, -caesar_key)
    
    return xor_result, final_result, ascii_values

def page_super_encryption():
    st.header("🔐 Super Enkripsi - Caesar + XOR")
    st.write("Tool untuk enkripsi dan dekripsi menggunakan kombinasi Caesar Cipher dan XOR Cipher")
    
    # ===== BAGIAN BARU: DEKRIPSI MOBIL =====
    if 'new_car_data' in st.session_state:
        st.success("🚗 Mobil baru berhasil ditambahkan! Sekarang isi deskripsi mobil:")
        
        car_data = st.session_state.new_car_data
        st.info(f"**Data Mobil:** {car_data['brand']} {car_data['model']} - Rp {car_data['price']:,}")
        
        with st.form("dekripsi_mobil_form"):
            deskripsi_text = st.text_area(
                "Deskripsi Mobil:", 
                placeholder="Masukkan deskripsi lengkap mobil...",
                help="Deskripsi ini akan dienkripsi dengan Super Encryption dan disimpan di database"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                caesar_key_desc = st.number_input(
                    "Kunci Caesar untuk Deskripsi:", 
                    min_value=-100, max_value=100, value=3,
                    key="caesar_desc"
                )
            with col2:
                xor_key_desc = st.text_input(
                    "Kunci XOR untuk Deskripsi:", 
                    value="mobil123",
                    key="xor_desc"
                )
            
            submit_desc = st.form_submit_button("💾 Simpan Deskripsi Mobil")
            
            if submit_desc and deskripsi_text:
                # Enkripsi deskripsi dengan Super Encryption
                caesar_result, final_result, ascii_values = super_encrypt(deskripsi_text, caesar_key_desc, xor_key_desc)
                
                # Simpan ke database (update kolom dekripsi_mobil)
                
                if update_car_dekripsi(car_data, final_result, car_data['encryption_key']):
                    st.success("✅ Deskripsi mobil berhasil disimpan dengan Super Encryption!")
                    # Hapus session state
                    del st.session_state.new_car_data
                    st.rerun()
                else:
                    st.error("❌ Gagal menyimpan deskripsi mobil!")
    
    # ===== BAGIAN ASLI SUPER ENCRYPTION =====
    st.write("---")    
    mode = st.radio("Pilih Mode:", ["Enkripsi", "Dekripsi"])
    text_input = st.text_area("Masukkan teks:")
    
    col1, col2 = st.columns(2)
    with col1:
        caesar_key = st.number_input("Kunci Caesar:", min_value=-100, max_value=100, value=3)
    with col2:
        xor_key = st.text_input("Kunci XOR:", value="secret", help="Kunci untuk XOR cipher")
    
    show_ascii = st.checkbox("📊 Tampilkan Detail Proses", value=True)
    
    if st.button(f"🚀 Jalankan {mode}"):
        if not text_input:
            st.warning("Masukkan teks terlebih dahulu!")
            return
        
        if not xor_key:
            st.warning("Masukkan kunci XOR!")
            return
        
        if mode == "Enkripsi":
            st.subheader("🔒 Hasil Enkripsi")
            caesar_result, final_result, ascii_values = super_encrypt(text_input, caesar_key, xor_key)
            
            # Tampilkan hasil
            st.success("✅ Enkripsi berhasil!")
            
            if show_ascii:
                col_step1, col_step2 = st.columns(2)
                
                with col_step1:
                    st.write("**Step 1 - Caesar Cipher:**")
                    st.code(f"Input: {text_input}")
                    st.code(f"Setelah Caesar (shift {caesar_key}): {caesar_result}")
                    
                    st.write("**ASCII Caesar Result:**")
                    caesar_ascii = [ord(c) for c in caesar_result]
                    st.code(caesar_ascii)
                    st.caption(f"Panjang: {len(caesar_ascii)} karakter")
                
                with col_step2:
                    st.write("**Step 2 - XOR Cipher (dengan Base64):**")
                    st.code(f"Setelah XOR + Base64: {final_result}")
                    
                    st.write("**ASCII XOR Result (sebelum Base64):**")
                    st.code(ascii_values)
                    st.caption(f"Panjang: {len(ascii_values)} karakter")
            
            # Hasil final
            st.write("**🎯 Hasil Final Enkripsi:**")
            st.text_area("Salin hasil enkripsi:", value=final_result, height=100, key="encrypted_result")
            
            # Tampilkan format data dalam expander
            with st.expander("📋 Detail Format Data"):
                col_format1, col_format2 = st.columns(2)
                
                with col_format1:
                    st.write("**Hexadecimal:**")
                    hex_result = ' '.join([f"{b:02x}" for b in ascii_values])
                    st.code(hex_result)
                    
                    st.write("**Binary:**")
                    binary_result = ' '.join([format(b, '08b') for b in ascii_values])
                    st.code(binary_result)
                
                with col_format2:
                    st.write("**Decimal (untuk programming):**")
                    st.code(str(ascii_values))
                    
                    st.write("**Panjang Data:**")
                    st.info(f"Input: {len(text_input)} karakter → Output: {len(final_result)} karakter")
            
        else:  # Mode Dekripsi
            st.subheader("🔓 Hasil Dekripsi")
            
            # Cek format input
            is_base64 = False
            try:
                # Coba decode sebagai Base64
                decoded = base64.b64decode(text_input)
                is_base64 = True
            except:
                is_base64 = False
            
            xor_result, final_result, ascii_values = super_decrypt(text_input, caesar_key, xor_key)
            
            st.success("✅ Dekripsi berhasil!")
            
            if show_ascii:
                col_step1, col_step2 = st.columns(2)
                
                with col_step1:
                    st.write("**Step 1 - XOR Decrypt:**")
                    st.code(f"Input: {text_input}")
                    st.code(f"Format terdeteksi: {'Base64' if is_base64 else 'Legacy'}")
                    st.code(f"Setelah XOR decrypt: {xor_result}")
                    
                    st.write("**ASCII XOR Result:**")
                    st.code(ascii_values)
                    st.caption(f"Panjang: {len(ascii_values)} karakter")
                
                with col_step2:
                    st.write("**Step 2 - Caesar Decrypt:**")
                    st.code(f"Setelah Caesar (shift -{caesar_key}): {final_result}")
                    
                    st.write("**ASCII Final Result:**")
                    final_ascii = [ord(c) for c in final_result]
                    st.code(final_ascii)
                    st.caption(f"Panjang: {len(final_ascii)} karakter")
            
            # Hasil final
            st.write("**🎯 Hasil Final Dekripsi:**")
            st.text_area("Salin hasil dekripsi:", value=final_result, height=100, key="decrypted_result")
            
            # Tampilkan format data dalam expander
            with st.expander("📋 Detail Format Data"):
                col_format1, col_format2 = st.columns(2)
                
                with col_format1:
                    st.write("**Hexadecimal:**")
                    hex_result = ' '.join([f"{b:02x}" for b in ascii_values])
                    st.code(hex_result)
                    
                    st.write("**Binary:**")
                    binary_result = ' '.join([format(b, '08b') for b in ascii_values])
                    st.code(binary_result)
                
                with col_format2:
                    st.write("**Decimal (untuk programming):**")
                    st.code(str(ascii_values))
                    
                    st.write("**Panjang Data:**")
                    st.info(f"Input: {len(text_input)} karakter → Output: {len(final_result)} karakter")

if __name__ == "__main__":
    page_super_encryption()