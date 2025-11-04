import streamlit as st
import hashlib
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

def encrypt_file(file_bytes: bytes, key: str) -> tuple[bytes, bytes]:
    """Enkripsi file menggunakan AES-128."""
    # Generate key dan iv - AES-128 butuh 16 byte key
    key = hashlib.sha256(key.encode()).digest()[:16]  # Ambil 16 byte pertama
    iv = get_random_bytes(AES.block_size)
    
    # Setup cipher
    cipher = AES.new(key, AES.MODE_CBC, iv)
    
    # Encrypt
    encrypted = cipher.encrypt(pad(file_bytes, AES.block_size))
    return encrypted, iv

def decrypt_file(encrypted_bytes: bytes, iv: bytes, key: str) -> bytes:
    """Dekripsi file menggunakan AES-128."""
    # Generate key - AES-128 butuh 16 byte key
    key = hashlib.sha256(key.encode()).digest()[:16]  # Ambil 16 byte pertama
    
    # Setup cipher
    cipher = AES.new(key, AES.MODE_CBC, iv)
    
    # Decrypt
    decrypted = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
    return decrypted

def page_file_encryption():
    st.subheader("File Encryption/Decryption")
    
    mode = st.radio("Mode", ["Enkripsi File", "Dekripsi File"])
    
    if mode == "Enkripsi File":
        uploaded_file = st.file_uploader("Pilih file untuk dienkripsi", type=['txt', 'pdf', 'doc', 'docx'])
        key = st.text_input("Masukkan password enkripsi", type="password")
        
        if uploaded_file and key:
            if st.button("Enkripsi File"):
                try:
                    # Read file
                    file_bytes = uploaded_file.read()
                    
                    # Encrypt
                    encrypted, iv = encrypt_file(file_bytes, key)
                    
                    # Combine IV and encrypted data
                    combined = base64.b64encode(iv + encrypted).decode('utf-8')
                    
                    # Save encrypted file
                    st.download_button(
                        label="Download Encrypted File",
                        data=combined.encode(),
                        file_name=f"encrypted_{uploaded_file.name}",
                        mime="application/octet-stream"
                    )
                    st.success("File berhasil dienkripsi!")
                    
                except Exception as e:
                    st.error(f"Error dalam enkripsi: {str(e)}")
    else:
        uploaded_file = st.file_uploader("Pilih file terenkripsi", type=None)
        key = st.text_input("Masukkan password dekripsi", type="password")
        file_type = st.selectbox("Tipe file asli", ['txt', 'pdf', 'doc', 'docx'])
        
        if uploaded_file and key:
            if st.button("Dekripsi File"):
                try:
                    # Read encrypted data
                    combined = base64.b64decode(uploaded_file.read())
                    
                    # Split IV and encrypted data
                    iv = combined[:AES.block_size]
                    encrypted = combined[AES.block_size:]
                    
                    # Decrypt
                    decrypted = decrypt_file(encrypted, iv, key)
                    
                    # Save decrypted file
                    st.download_button(
                        label="Download Decrypted File",
                        data=decrypted,
                        file_name=f"decrypted_file.{file_type}",
                        mime="application/octet-stream"
                    )
                    st.success("File berhasil didekripsi!")
                    
                except Exception as e:
                    st.error(f"Error dalam dekripsi: {str(e)}")
