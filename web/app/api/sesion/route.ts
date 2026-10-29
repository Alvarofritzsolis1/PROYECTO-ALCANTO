import { autorizado, cerrarSesion, configurado, denegado, iniciarSesion } from "@/lib/auth";
import { almacenamientoListo } from "@/lib/blob";

export const runtime="nodejs";
export async function GET(){
 return Response.json({
  sesion: await autorizado(), instalado:configurado(),
  almacenamiento:almacenamientoListo(),
  motor: Boolean(process.env.ASPOSE_CLIENT_ID && process.env.ASPOSE_CLIENT_SECRET)
 },{headers:{"Cache-Control":"no-store"}});
}
export async function POST(req:Request){
 let pass="";
 try{pass=String((await req.json()).password||"");}catch{return Response.json({error:"Solicitud incorrecta"},{status:400});}
 if(!(await iniciarSesion(pass)))return Response.json({error:"Contraseña incorrecta o aplicación sin configurar"},{status:401});
 return Response.json({ok:true});
}
export async function DELETE(){
 if(!(await autorizado()))return denegado();
 await cerrarSesion();return Response.json({ok:true});
}
