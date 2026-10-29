export async function convertirPdf(archivo:Uint8Array,hoja:string):Promise<Uint8Array>{
 const id=process.env.ASPOSE_CLIENT_ID;
 const secret=process.env.ASPOSE_CLIENT_SECRET;
 if(!id||!secret)throw new Error("Falta configurar el motor Aspose.Cells Cloud.");
 const credenciales=new URLSearchParams({grant_type:"client_credentials",client_id:id,client_secret:secret});
 const auth=await fetch("https://api.aspose.cloud/connect/token",{
  method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded","Accept":"application/json"},
  body:credenciales,cache:"no-store",signal:AbortSignal.timeout(30000)
 });
 if(!auth.ok)throw new Error("Aspose no autorizó la conexión ("+auth.status+").");
 const token=(await auth.json()).access_token as string;
 if(!token) throw new Error("Aspose no entregó token de acceso.");
 const form=new FormData();
 form.set("Spreadsheet",new Blob([new Uint8Array(archivo)],{type:"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}),"ALCANTO_copia_temporal.xlsx");
 const ruta="https://api.aspose.cloud/v4.0/cells/convert/worksheet/pdf?worksheet="+encodeURIComponent(hoja)+"&region=es-CL";
 const pdf=await fetch(ruta,{
  method:"PUT",headers:{Authorization:"Bearer "+token,Accept:"application/pdf"},
  body:form,cache:"no-store",signal:AbortSignal.timeout(115000)
 });
 if(!pdf.ok) {
  const detalle=(await pdf.text()).slice(0,300);
  throw new Error("El motor PDF no pudo convertir la hoja ("+pdf.status+"): "+detalle);
 }
 const data=new Uint8Array(await pdf.arrayBuffer());
 if(data.length<100 || String.fromCharCode(...data.slice(0,4))!=="%PDF")
  throw new Error("Respuesta de conversión inválida: PDF no detectado.");
 if(data.length>4_000_000)
  throw new Error("PDF excede el límite directo de descarga. Requiere almacenamiento privado de salida.");
 return data;
}
