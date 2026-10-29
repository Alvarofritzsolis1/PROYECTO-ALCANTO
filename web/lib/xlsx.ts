import { unzipSync, zipSync, strToU8, strFromU8 } from "fflate";
import { CAMPOS } from "./fields";

export type ArchivoZip = Record<string, Uint8Array>;
function escapeXml(s:string){
 return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&apos;");
}
export function abrirXlsx(bytes:Uint8Array):ArchivoZip {
 if(bytes.length>25*1024*1024)throw new Error("Plantilla demasiado grande.");
 if(bytes[0]!==80||bytes[1]!==75)throw new Error("La plantilla no parece un .xlsx.");
 const zip=unzipSync(bytes);
 for(const nombre of ["xl/workbook.xml","xl/worksheets/sheet1.xml","xl/worksheets/sheet13.xml"]){
  if(!zip[nombre])throw new Error("Falta parte del archivo XLSX: "+nombre);
 }
 const workbook=strFromU8(zip["xl/workbook.xml"]);
 if(!workbook.includes("Datos Contrato") || !workbook.includes("MATRIZ PTS"))
  throw new Error("La plantilla no corresponde al proyecto ALCANTO.");
 return zip;
}
function celdaRegex(ref:string){
 return new RegExp('(<c\\b[^>]*\\br="'+ref+'"[^>]*>)([\\s\\S]*?)(<\\/c>)');
}
export function sustituirEntradas(template:Uint8Array, datos:Record<string,string>):Uint8Array{
 const zip=abrirXlsx(template);
 let xml=strFromU8(zip["xl/worksheets/sheet1.xml"]);
 for(const [ref,valor] of Object.entries(datos)){
  if(!(ref in CAMPOS)) throw new Error("Celda no permitida: "+ref);
  if(typeof valor!=="string" || valor.length>500)throw new Error("Dato no válido: "+ref);
  const rx=celdaRegex(ref);
  const match=xml.match(rx);
  if(!match)throw new Error("La celda "+ref+" no existe en la plantilla.");
  if(/<(?:[A-Za-z0-9_]+:)?f(?:\s|>)/.test(match[2]))
   throw new Error("La celda "+ref+" tiene fórmula: NO será modificada.");
  const numeric=ref==="C32";
  if(numeric && !/^\d{1,12}$/.test(valor))throw new Error("Sueldo debe contener solo números.");
  const tag=match[1].replace(/\\s+t="[^"]*"/g,"").replace(/>$/,numeric?">":' t="inlineStr">');
  const body=numeric? "<v>"+valor+"</v>": '<is><t xml:space="preserve">'+escapeXml(valor)+"</t></is>";
  xml=xml.replace(rx,()=>tag+body+"</c>");
 }
 zip["xl/worksheets/sheet1.xml"]=strToU8(xml);
 let libro=strFromU8(zip["xl/workbook.xml"]);
 if(/<calcPr\b[^>]*\/>/.test(libro)){
  libro=libro.replace(/<calcPr\b[^>]*\/>/,m=>{
   return m.replace(/\s+fullCalcOnLoad="[^"]*"/g,"").replace(/\s+forceFullCalc="[^"]*"/g,"").replace(/\s+calcMode="[^"]*"/g,"").replace(/\/>$/, ' fullCalcOnLoad="1" forceFullCalc="1" calcMode="auto"/>');
  });
 }else{
  libro=libro.replace(/<\/workbook>/,'<calcPr fullCalcOnLoad="1" forceFullCalc="1" calcMode="auto"/></workbook>');
 }
 zip["xl/workbook.xml"]=strToU8(libro);
 return zipSync(zip,{level:6});
}
export function ptsCompleto(template:Uint8Array,cargo:string):boolean{
 if(!cargo.trim()) return false;
 const zip=abrirXlsx(template);
 const xml=strFromU8(zip["xl/worksheets/sheet13.xml"]);
 const objetivo=cargo.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toUpperCase().trim();
 const rows=xml.matchAll(/<row\b[^>]*\br="(\d+)"[^>]*>([\s\S]*?)<\/row>/g);
 for(const match of rows){
  const fila=Number(match[1]);
  if(fila<2||fila>27)continue;
  const contenido=match[2];
  const clave=contenido.match(celdaRegex("A"+fila));
  const cache=clave?.[2].match(/<v>([\s\S]*?)<\/v>/);
  const actual=(cache?.[1]||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toUpperCase().trim();
  if(actual!==objetivo)continue;
  for(let col=68;col<=84;col++){
   const ref=String.fromCharCode(col)+fila;
   const celda=contenido.match(celdaRegex(ref));
   if(!celda || !/(<v>[^<]+<\/v>|<is>[\s\S]*?<t[^>]*>[^<]+<\/t>)/.test(celda[2]))return false;
  }
  return true;
 }
 return false;
}
