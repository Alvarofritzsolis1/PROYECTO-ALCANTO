import { autorizado, denegado } from "@/lib/auth";
import { RUTA_PLANTILLA } from "@/lib/blob";
import { head } from "@vercel/blob";

export const runtime="nodejs";
export async function GET(){
 if(!(await autorizado()))return denegado();
 try{
  const blob=await head(RUTA_PLANTILLA);
  return Response.json({cargada:!!blob,archivo:blob?.pathname,size:blob?.size},{headers:{"Cache-Control":"no-store"}});
 }catch{return Response.json({cargada:false},{headers:{"Cache-Control":"no-store"}});}
}
