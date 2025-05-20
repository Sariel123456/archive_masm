import os
from cryptography.fernet import Fernet

FERNET_KEY = os.environ.get('FERNET_KEY')
if not FERNET_KEY:
    raise Exception("FERNET_KEY n'est pas définie dans les variables d'environnement")
fernet = Fernet(FERNET_KEY.encode())

def encrypt_file(file_data):
    return fernet.encrypt(file_data)

def decrypt_file(file_data):
    return fernet.decrypt(file_data)