from hashlib import sha256

texto = """
Nombre: Juan Perez
Curso: Power BI
Institucion: INFOTEP
"""

hash_certificado = sha256(texto.encode()).hexdigest()

print(hash_certificado)