import { get, put, list } from "@vercel/blob";
import { randomUUID } from "node:crypto";
import { validarDatos } from "./fields";

export const RUTA_PLANTILLA = "plantillas/alcanto.xlsx";
export type Registro={ id:string; creado:string; datos:Record<string,string> };

export function almacenamientoListo(){return Boolean(process.env.BLOB_READ_WRITE_TOKEN);}
export async function obtenerPlantilla():Promise<Uint8Array>{
 const resultado=await get(RUTA_PLANTILLA,{access:"private"});
 if(!resultado?.stream) throw new Error("Primero hay que cargar la plantilla XLSX en el almacenamiento privado.");
 const array=await new Response(resultado.stream).arrayBuffer();
 if(array.byteLength>25*1024*1024) throw new Error("La plantilla supera el tamaño previsto.");
 return new Uint8Array(array);
}
export async function guardarRegistro(datos:unknown):Promise<Registro>{
 const validos=validarDatos(datos);
 if(!validos.C5||!validos.C17||!validos.C18)throw new Error("Empresa, nombre y RUT de trabajador son obligatorios.");
 const doc:Registro={id:randomUUID(),creado:new Date().toISOString(),datos:validos};
 await put("registros/"+doc.id+".json",JSON.stringify(doc),{access:"private",contentType:"application/json",addRandomSuffix:false});
 return doc;
}
export async function leerRegistro(id:string):Promise<Registro>{
 if(!/^[0-9a-f-]{36}$/.test(id))throw new Error("Identificador inválido");
 const archivo=await get("registros/"+id+".json",{access:"private"});
 if(!archivo?.stream) throw new Error("Registro no encontrado.");
 const d=JSON.parse(await new Response(archivo.stream).text());
 return {id:d.id,creado:d.creado,datos:validarDatos(d.datos)};
}
export async function listarRegistros():Promise<Array<{id:string;creado:string;empresa:string;trabajador:string;rut:string;cargo:string}>>{
 const res=await list({prefix:"registros/",limit:100});
 const archivos=res.blobs.filter(b=>b.pathname.endsWith(".json")).slice(0,50);
 const datos=await Promise.all(archivos.map(async item=>{
  try{
   const archivo=await get(item.pathname,{access:"private"});
   if(!archivo?.stream)return null;
   const d=JSON.parse(await new Response(archivo.stream).text()) as Registro;
   return {id:d.id,creado:d.creado,empresa:d.datos.C5||"",trabajador:d.datos.C17||"",rut:d.datos.C18||"",cargo:d.datos.C29||""};
  }catch{return null;}
 }));
 return datos.filter((r):r is NonNullable<typeof r>=>Boolean(r)).sort((a,b)=>b.creado.localeCompare(a.creado));
}
