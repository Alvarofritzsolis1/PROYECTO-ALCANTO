import { autorizado, denegado } from "@/lib/auth";
import { handleUpload } from "@vercel/blob/client";
import { RUTA_PLANTILLA } from "@/lib/blob";

export const runtime="nodejs";
export async function POST(req:Request){
 if(!(await autorizado()))return denegado();
 try{
  const data=await req.json();
  const response=await handleUpload({
   body:data,request:req,
   onBeforeGenerateToken:async pathname=>{
    if(pathname!==RUTA_PLANTILLA) throw new Error("Ruta de plantilla no autorizada.");
    return {
      allowedContentTypes:["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
      maximumSizeInBytes:25*1024*1024,
      addRandomSuffix:false,
      allowOverwrite:true,
    };
   },
   onUploadCompleted:async()=>{}
  });
  return Response.json(response);
 }catch(e){return Response.json({error:(e as Error).message},{status:400});}
}
