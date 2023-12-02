from cryptography.fernet import Fernet

class Login_Cryptography:
    def __init__(self, *args, **kwargs):
        self.info = """
        Description: This program will read the key and encrypted pwd generated
        by GenerateEncryptedKey program. Can be executed multiple time.
        """
        
    def decrypt(self, text, key):
        """"
        Description: This program will read the key and encrypted pwd generated
        by GenerateEncryptedKey program. Can be executed multiple time.
        """
        ### 1. read encrypted pwd and convert into byte
        encpwdbyt = text
        ### 2. read key and convert into byte
        refKeybyt = key
        ### 3. use the key and encrypt pwd
        keytouse = Fernet(refKeybyt)
        myPass = (keytouse.decrypt(encpwdbyt))
        
        return str(myPass.decode('utf-8'))
        
    def encrypt_it(self, text: str):
        """
        Encrypts a string that was passed to this function
        
        Returns: key -> string
                 encryption -> string
        """
        from cryptography.fernet import Fernet
        ### 1. generate key and write it in a file
        key = Fernet.generate_key()
        ### 2. encrypt the password and write it in a file
        refKey = Fernet(key)
        mypwdbyt = bytes(text, 'utf-8') # convert into byte
        encryptedPWD = refKey.encrypt(mypwdbyt)
        ### 3. return key and encrypted password
        return key, encryptedPWD
        