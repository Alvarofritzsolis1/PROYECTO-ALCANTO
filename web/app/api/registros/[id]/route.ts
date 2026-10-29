import { autorizado, denegado } from "@/lib/auth";
import { leerRegistro } from "@/lib/blob";
export const runtime="nodejs";
export async function GET(_req:Request,{params}:{params:Promise<{id:string}>}){
 if(!(await autorizado()))return denegado();
 try{
  const {id}=await params;
  return Response.json({registro:await leerRegistro(id)},{headers:{"Cache-Control":"no-store"}});
 }catch(e){return Response.json({error:(e as Error).message},{status:404});}
}
