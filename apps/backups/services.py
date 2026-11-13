
import os
import base64
import tempfile
import subprocess

from django.conf import settings
from django.db import connection

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def generar_backup():
    configuracion = connection.settings_dict

    if configuracion["ENGINE"] != "django.db.backends.postgresql":
        raise RuntimeError("La base de datos debe ser PostgreSQL.")

    clave_configurada = settings.BACKUP_ENCRYPTION_KEY

    if not clave_configurada:
        raise RuntimeError("No está configurada la clave de cifrado.")

    try:
        clave = base64.urlsafe_b64decode(clave_configurada)
    except Exception as error:
        raise RuntimeError("La clave de cifrado no es válida.") from error

    if len(clave) != 32:
        raise RuntimeError("La clave debe contener 32 bytes.")

    ruta_original = None
    ruta_cifrada = None

    try:
        # Crear archivo temporal de PostgreSQL
        with tempfile.NamedTemporaryFile(
            suffix=".dump",
            delete=False,
        ) as archivo:
            ruta_original = archivo.name

        entorno = os.environ.copy()

        if configuracion.get("PASSWORD"):
            entorno["PGPASSWORD"] = configuracion["PASSWORD"]

        comando = [
            "pg_dump",
            "-h", configuracion["HOST"] or "localhost",
            "-p", str(configuracion["PORT"] or "5432"),
            "-U", configuracion["USER"],
            "-d", configuracion["NAME"],
            "-F", "c",
            "-b",
            "-f", ruta_original,
        ]

        subprocess.run(
            comando,
            env=entorno,
            check=True,
            capture_output=True,
            text=True,
        )

        # Crear archivo cifrado
        with tempfile.NamedTemporaryFile(
            suffix=".dump.enc",
            delete=False,
        ) as archivo:
            ruta_cifrada = archivo.name

        nonce = os.urandom(12)

        cifrador = Cipher(
            algorithms.AES(clave),
            modes.GCM(nonce),
        ).encryptor()

        with open(ruta_original, "rb") as original:
            with open(ruta_cifrada, "wb") as destino:

                # Identificador del formato y nonce
                destino.write(b"CITAHN-ENC-v1")
                destino.write(nonce)

                while True:
                    bloque = original.read(1024 * 1024)

                    if not bloque:
                        break

                    destino.write(cifrador.update(bloque))

                destino.write(cifrador.finalize())

                # Etiqueta de autenticación
                destino.write(cifrador.tag)

        return ruta_cifrada

    except Exception:
        if ruta_cifrada and os.path.exists(ruta_cifrada):
            os.remove(ruta_cifrada)
        raise

    finally:
        if ruta_original and os.path.exists(ruta_original):
            os.remove(ruta_original)
