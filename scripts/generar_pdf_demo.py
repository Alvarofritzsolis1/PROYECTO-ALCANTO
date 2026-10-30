"""Genera muestras ficticias de los 10 PDF web; solo para pruebas CI."""
from __future__ import annotations
from datetime import date
from pathlib import Path
from alcanto_cloud.catalog import DOCUMENTOS
from alcanto_cloud.documentos import preparar_datos, HOJAS_EMPRESA
from alcanto_cloud.pdf_web import generar_pdf_web
from alcanto_cloud.pdf_service import validar_pdf

EMPRESA={
    "C5":"CONSTRUCTORA DE EJEMPLO ALCANTO SPA",
    "C6":"76.111.222-3", "C7":"REPRESENTANTE FICTICIO",
    "C8":"12.222.333-4", "C10":"AVENIDA FICTICIA 100",
    "C12":"CONCEPCIÓN", "C14":"OBRAS CIVILES",
    "D30":"Lomas Verdes", "DECLARANTE_NACIONALIDAD":"CHILENA",
}
TRABAJADOR={
    "C17":"TRABAJADOR DEMOSTRACIÓN", "C18":"11.111.111-1",
    "C19":"CHILENA", "C20":"1995-01-01", "C21":"SOLTERO",
    "C22":"CALLE FICTICIA 200", "C29":"PINTOR",
    "C31":"42", "C32":"640000", "C34":"MENSUALMENTE",
    "C38":"HABITAT", "C39":"FONASA", "C43":"Faenas Lomas Verdes",
    "ANEXO_M4":"2027-04-30",
}
destino=Path("artifacts/alcanto_pdf_demo")
destino.mkdir(parents=True,exist_ok=True)
for numero,doc in enumerate(DOCUMENTOS,1):
    worker=None if doc.hoja in HOJAS_EMPRESA else TRABAJADOR
    datos=preparar_datos(EMPRESA,worker,hoja=doc.hoja,cargo_pts="PINTOR")
    pdf=generar_pdf_web(doc.hoja,datos,fecha=date(2026,11,1),confirma_jurada=True)
    validacion=validar_pdf(pdf,doc.hoja)
    name=doc.hoja.replace(" ","_").replace(".","")
    output=destino / f"{numero:02d}_{name}.pdf"
    output.write_bytes(pdf)
    print(f"{output}: {validacion.paginas} páginas, {len(pdf)} bytes")
print("Total: 10 PDF de prueba. Todos los datos son ficticios.")
