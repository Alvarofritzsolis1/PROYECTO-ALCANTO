"""Instalación inicial del modelo maestro en almacenamiento S3 PRIVADO.

Este script es exclusivo para administración y NO se ejecuta para visitantes.
El libro original se conserva intacto y sus fórmulas no se cambian.
"""
from __future__ import annotations

import argparse
import os
from hashlib import sha256
from pathlib import Path

from alcanto_cloud.workbook import generar_copia, verificar_plantilla

KEY = "alcanto/plantilla_maestra.xlsx"


def preparar(ruta: Path) -> bytes:
    original = ruta.read_bytes()
    antes = verificar_plantilla(original)
    copia = generar_copia(original, {}, limpiar_previos=True)
    despues = verificar_plantilla(copia)
    if antes["formulas_totales"] != despues["formulas_totales"]:
        raise RuntimeError("El total de fórmulas cambió; aprovisionamiento cancelado.")
    if len(despues["hojas"]) != 17:
        raise RuntimeError("No se encontraron las 17 hojas de ALCANTO.")
    if sha256(original).digest() == sha256(copia).digest():
        raise RuntimeError("No se generó una copia limpia de las entradas.")
    return copia


def subir_privado(datos: bytes) -> None:
    import boto3
    configuracion = {
        "aws_access_key_id": os.environ["AWS_ACCESS_KEY_ID"],
        "aws_secret_access_key": os.environ["AWS_SECRET_ACCESS_KEY"],
        "region_name": os.environ.get("ALCANTO_S3_REGION", "auto"),
    }
    endpoint = os.environ.get("ALCANTO_S3_ENDPOINT_URL", "")
    if endpoint:
        if not endpoint.startswith("https://"):
            raise ValueError("El almacenamiento privado necesita HTTPS.")
        configuracion["endpoint_url"] = endpoint
    bucket = os.environ["ALCANTO_S3_BUCKET"]
    cliente = boto3.client("s3", **configuracion)
    cliente.put_object(
        Bucket=bucket, Key=KEY, Body=datos,
        ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ServerSideEncryption="AES256",
        Metadata={"alcanto-template": "read-only"},
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Instalar plantilla ALCANTO una vez, fuera de la web")
    parser.add_argument("excel", type=Path, help="Ruta para el administrador, no para un visitante")
    parser.add_argument("--confirmar-upload", action="store_true", help="Subir al bucket privado")
    args = parser.parse_args()
    datos = preparar(args.excel)
    print("Copia del modelo validada: 17 hojas y fórmulas conservadas.")
    print("IMPORTANTE: podrían quedar cachés y metadatos personales de la fuente; usar almacenamiento privado.")
    if not args.confirmar_upload:
        print("Validación local terminada: nada se subió.")
        return
    subir_privado(datos)
    print("Modelo interno cargado en S3 privado. La web ya no solicitará el Excel a los usuarios.")


if __name__ == "__main__":
    main()
