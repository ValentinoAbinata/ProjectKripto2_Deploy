import streamlit as st
import hashlib
import secrets
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# ===== FUNGSI CHACHA20 =====
def derive_chacha_key(user_key):
    """Derive 32-byte key from user input using SHA256"""
    return hashlib.sha256(user_key.encode()).digest()

def encrypt_chacha20(text, user_key):
    """Encrypt text using ChaCha20 algorithm with user key"""
    try:
        # Derive key from user input
        key = derive_chacha_key(user_key)
        
        # Generate random nonce (16 bytes for ChaCha20)
        nonce = secrets.token_bytes(16)
        
        # Convert text to bytes
        text_bytes = text.encode('utf-8')
        
        # Create ChaCha20 cipher
        algorithm = algorithms.ChaCha20(key, nonce)
        cipher = Cipher(algorithm, mode=None, backend=default_backend())
        encryptor = cipher.encryptor()
        
        # Encrypt the text
        ciphertext = encryptor.update(text_bytes) + encryptor.finalize()
        
        # Combine nonce + ciphertext and encode as base64
        encrypted_data = nonce + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    except Exception as e:
        st.error(f"Encryption error: {e}")
        return None

def decrypt_chacha20(encrypted_text, user_key):
    """Decrypt text using ChaCha20 algorithm with user key - always return result even if wrong key"""
    try:
        if not encrypted_text:
            return "[EMPTY]"
            
        # Derive key from user input
        key = derive_chacha_key(user_key)
        
        # Decode from base64
        try:
            encrypted_data = base64.b64decode(encrypted_text.encode('utf-8'))
        except Exception:
            # Try adding padding if necessary
            try:
                padding = 4 - (len(encrypted_text) % 4)
                if padding != 4:
                    encrypted_text += "=" * padding
                encrypted_data = base64.b64decode(encrypted_text.encode('utf-8'))
            except Exception as e:
                return f"[BASE64_ERROR: {str(e)}]"
        
        # Extract nonce (first 16 bytes) and ciphertext
        if len(encrypted_data) < 16:
            return f"[DATA_TOO_SHORT: {len(encrypted_data)} bytes]"
            
        nonce = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        
        # Create ChaCha20 cipher
        algorithm = algorithms.ChaCha20(key, nonce)
        cipher = Cipher(algorithm, mode=None, backend=default_backend())
        decryptor = cipher.decryptor()
        
        # Decrypt the text
        decrypted_bytes = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Try to decode as UTF-8
        try:
            result = decrypted_bytes.decode('utf-8')
            # Check if result contains unusual characters that might indicate wrong key
            if any(ord(c) > 127 for c in result) and len(result) > 0:
                return f"[POSSIBLE_WRONG_KEY: {result}]"
            return result
        except UnicodeDecodeError:
            # Return raw bytes as string for wrong key
            return f"[DECODE_ERROR: {decrypted_bytes.hex()[:50]}...]"
    
    except Exception as e:
        return f"[DECRYPTION_ERROR: {str(e)}]"

# ===== FUNGSI SUPER ENCRYPTION =====
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

def xor_cipher(text, key):
    result = ""
    key_length = len(key)
    for i, char in enumerate(str(text)):
        key_char = key[i % key_length]
        xor_result = ord(char) ^ ord(key_char)
        result += chr(xor_result)
    return result

def xor_cipher_with_ascii(text, key):
    """XOR cipher dengan return tambahan: result string dan list ASCII"""
    result = ""
    ascii_values = []
    key_length = len(key)
    for i, char in enumerate(str(text)):
        key_char = key[i % key_length]
        xor_result = ord(char) ^ ord(key_char)
        result += chr(xor_result)
        ascii_values.append(xor_result)
    return result, ascii_values

def super_encrypt(text, caesar_key, xor_key):
    """Super encrypt dengan return tambahan untuk ASCII values"""
    caesar_result = caesar_cipher(text, caesar_key)
    final_result, ascii_values = xor_cipher_with_ascii(caesar_result, xor_key)
    return caesar_result, final_result, ascii_values

def super_decrypt(encrypted_text, caesar_key, xor_key):
    """Super decrypt dengan return tambahan untuk ASCII values"""
    xor_result, ascii_values = xor_cipher_with_ascii(encrypted_text, xor_key)
    final_result = caesar_cipher(xor_result, -caesar_key)
    return xor_result, final_result, ascii_values