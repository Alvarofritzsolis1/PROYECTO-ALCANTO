import { autorizado, denegado } from "@/lib/auth";
import { leerRegistro, obtenerPlantilla } from "@/lib/blob";
import { DOCUMENTOS } from "@/lib/fields";
import { ptsCompleto, sustituirEntradas } from "@/lib/xlsx";
import { convertirPdf } from "@/lib/aspose";

export const runtime="nodejs";
export const maxDuration=120;
export async function POST(req:Request){
 if(!(await autorizado()))return denegado();
 try{
  const entrada=await req.json();
  const {id,hoja,confirmado}=entrada||{};
  if(!id || typeof hoja!=="string" || !(hoja in DOCUMENTOS)|| confirmado!==true)
   return Response.json({error:"Escoge un documento y confirma la revisión."},{status:400});
  const registro=await leerRegistro(id);
  const requisito=DOCUMENTOS[hoja];
  const faltan=requisito.requeridos.filter(ref=>!registro.datos[ref]);
  if(faltan.length)return Response.json({error:"Faltan campos: "+faltan.join(", ")},{status:422});
  const template=await obtenerPlantilla();
  if(hoja==="PTS." && !ptsCompleto(template,registro.datos.C29||""))
   return Response.json({error:"Este cargo todavía no tiene completo su contenido PTS."},{status:422});
  const archivo=sustituirEntradas(template,registro.datos);
  const pdf=await convertirPdf(archivo,hoja);
  const nombre="ALCANTO_"+hoja.replace(/[^\p{L}\p{N} ._-]/gu,"_").replace(/\s+/g,"_")+".pdf";
  return new Response(Buffer.from(pdf),{
   status:200,headers:{"Content-Type":"application/pdf","Content-Disposition":'attachment; filename="'+nombre+'"',"Cache-Control":"no-store","X-Content-Type-Options":"nosniff"}
  });
 }catch(e){return Response.json({error:(e as Error).message},{status:502,headers:{"Cache-Control":"no-store"}});}
}
