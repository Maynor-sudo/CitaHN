import os
import tempfile
from django.conf import settings
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def desencriptar_backup(ruta_enc):
    clave = settings.BACKUP_ENCRYPTION_KEY

    if not clave:
        raise RuntimeError("No existe una clave de cifrado configurada.")

    import base64

    clave = base64.urlsafe_b64decode(clave)

    if len(clave) != 32:
        raise RuntimeError("La clave AES-256 no es válida.")

    with open(ruta_enc, "rb") as archivo:
        encabezado = archivo.read(13)

        if encabezado != b"CITAHN-ENC-v1":
            raise ValueError("El archivo no tiene un formato válido.")

        nonce = archivo.read(12)

        if len(nonce) != 12:
            raise ValueError("El archivo está incompleto.")

        archivo.seek(0, os.SEEK_END)
        tamano = archivo.tell()

        if tamano < 13 + 12 + 16:
            raise ValueError("El archivo cifrado está incompleto.")

        archivo.seek(tamano - 16)
        tag = archivo.read(16)

        archivo.seek(25)
        contenido_cifrado = archivo.read(tamano - 25 - 16)

    descifrador = Cipher(
        algorithms.AES(clave),
        modes.GCM(nonce, tag),
    ).decryptor()

    contenido = descifrador.update(contenido_cifrado)
    contenido += descifrador.finalize()

    temporal = tempfile.NamedTemporaryFile(
        suffix=".dump",
        delete=False,
    )

    try:
        with temporal:
            temporal.write(contenido)

        return temporal.name

    except Exception:
        if os.path.exists(temporal.name):
            os.remove(temporal.name)
        raise
