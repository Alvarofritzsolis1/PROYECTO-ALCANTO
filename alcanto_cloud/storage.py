"""Repositorio privado S3 compatible (Amazon S3 / Cloudflare R2).

No almacena datos en GitHub ni logs de la nube. Sin configurar S3 la aplicación
permite modo sesión, que se pierde al reiniciar el servidor Streamlit.
"""
from __future__ import annotations

import json
from io import BytesIO
from uuid import uuid4
from datetime import datetime, timezone

import boto3
from botocore.config import Config

MAX_TEMPLATE = 25 * 1024 * 1024


class AlmacenPrivado:
    def __init__(self, cfg: dict):
        required = ("bucket", "access_key_id", "secret_access_key")
        if not all(cfg.get(c) for c in required):
            raise ValueError("Almacenamiento privado sin configurar: bucket y credenciales S3.")
        endpoint = cfg.get("endpoint_url") or None
        if endpoint and not endpoint.startswith("https://"):
            raise ValueError("La conexión al almacenamiento privado debe usar HTTPS.")
        self.bucket = cfg["bucket"]
        self.cliente = boto3.client("s3", endpoint_url=endpoint,
            aws_access_key_id=cfg["access_key_id"],
            aws_secret_access_key=cfg["secret_access_key"],
            region_name=cfg.get("region", "auto"),
            config=Config(signature_version="s3v4", retries={"max_attempts": 2},
                          connect_timeout=10, read_timeout=30))

    def guardar_plantilla(self, datos: bytes) -> None:
        if len(datos) > MAX_TEMPLATE:
            raise ValueError("Plantilla superior a 25 MB.")
        self.cliente.put_object(Bucket=self.bucket, Key="alcanto/plantilla_maestra.xlsx",
             Body=datos, ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    def obtener_plantilla(self) -> bytes | None:
        try:
            res = self.cliente.get_object(Bucket=self.bucket,Key="alcanto/plantilla_maestra.xlsx")
            if res["ContentLength"] > MAX_TEMPLATE: raise ValueError("Plantilla privada demasiado grande.")
            return res["Body"].read()
        except self.cliente.exceptions.NoSuchKey:
            return None
        except Exception as exc:
            if getattr(exc, "response", {}).get("Error", {}).get("Code") in ("NoSuchKey", "404"):
                return None
            raise

    def guardar(self, coleccion: str, datos: dict) -> str:
        if coleccion not in ("empresas", "trabajadores"):
            raise ValueError("Colección no autorizada.")
        identificador = str(uuid4())
        documento = {**datos, "id": identificador,
                     "creado": datetime.now(timezone.utc).isoformat()}
        contenido = json.dumps(documento,ensure_ascii=False).encode("utf-8")
        if len(contenido) > 15_000: raise ValueError("Registro demasiado grande.")
        self.cliente.put_object(Bucket=self.bucket, Key=f"alcanto/{coleccion}/{identificador}.json",
             Body=contenido,ContentType="application/json; charset=utf-8")
        return identificador

    def listar(self, coleccion: str) -> list[dict]:
        if coleccion not in ("empresas", "trabajadores"):
            raise ValueError("Colección no autorizada.")
        res=[]
        paginas=self.cliente.get_paginator("list_objects_v2").paginate(
            Bucket=self.bucket, Prefix=f"alcanto/{coleccion}/",PaginationConfig={"MaxItems":1000})
        for pagina in paginas:
            for entrada in pagina.get("Contents",[]):
                try:
                    obj=self.cliente.get_object(Bucket=self.bucket,Key=entrada["Key"])
                    if obj["ContentLength"]<=15_000:
                        res.append(json.loads(obj["Body"].read().decode("utf-8")))
                except Exception:
                    continue
        return sorted(res,key=lambda x:x.get("creado", ""),reverse=True)
