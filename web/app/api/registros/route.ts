import { autorizado, denegado } from "@/lib/auth";
import { guardarRegistro, listarRegistros } from "@/lib/blob";

export const runtime="nodejs";
export async function GET(){
 if(!(await autorizado()))return denegado();
 try{return Response.json({registros:await listarRegistros()},{headers:{"Cache-Control":"no-store"}});}
 catch(e){return Response.json({error:(e as Error).message},{status:503});}
}
export async function POST(request:Request){
 if(!(await autorizado()))return denegado();
 try{
  const body=await request.json();
  const registro=await guardarRegistro(body.datos);
  return Response.json({registro},{status:201});
 }catch(e){return Response.json({error:(e as Error).message},{status:400});}
}
