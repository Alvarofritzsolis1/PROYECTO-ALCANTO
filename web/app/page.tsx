"use client";
import { useEffect, useMemo, useState } from "react";
import { upload } from "@vercel/blob/client";
import { CAMPOS, DOCUMENTOS } from "@/lib/fields";

type VistaRegistro={id:string;empresa:string;trabajador:string;rut:string;cargo:string;creado:string};
const grupos=[
 ["Empresa y representante",["C5","C6","C7","C8","C9","C10","C11","C12","C13","C14"]],
 ["Datos del trabajador",["C17","C18","C19","C21","C22","C23","C24","C25","C26"]],
 ["Contrato, cargo y faena",["C29","D30","C31","C32","C34","C35","C38","C39","C43","C44"]],
] as const;
function datosCompletos(d:Record<string,string>, campos:string[]){return campos.filter(k=>!d[k]?.trim());}
async function jsonSeguro(resp:Response){
 const data=await resp.json().catch(()=>({error:"Respuesta inválida del servidor"}));
 if(!resp.ok) throw new Error(data.error||"Error "+resp.status);
 return data;
}

export default function Home(){
 const [sesion,setSesion]=useState(false),[instalado,setInstalado]=useState(false);
 const [almacenamiento,setAlmacenamiento]=useState(false),[motor,setMotor]=useState(false);
 const [pass,setPass]=useState(""),[plantilla,setPlantilla]=useState(false);
 const [cargando,setCargando]=useState(true),[ocupado,setOcupado]=useState(false);
 const [mensaje,setMensaje]=useState(""),[error,setError]=useState("");
 const [form,setForm]=useState<Record<string,string>>({});
 const [registros,setRegistros]=useState<VistaRegistro[]>([]);
 const [seleccionado,setSeleccionado]=useState("");
 const [hoja,setHoja]=useState("Contrato Imprimible"),[confirmado,setConfirmado]=useState(false);
 const [seccion,setSeccion]=useState("nuevo");

 async function cargar(){
  const sess=await fetch("/api/sesion",{cache:"no-store"}).then(r=>r.json());
  setSesion(sess.sesion);setInstalado(sess.instalado);setAlmacenamiento(sess.almacenamiento);setMotor(sess.motor);
  if(sess.sesion){
   const [p,r]=await Promise.all([
    fetch("/api/plantilla",{cache:"no-store"}).then(r=>r.json()).catch(()=>({cargada:false})),
    fetch("/api/registros",{cache:"no-store"}).then(r=>r.json()).catch(()=>({registros:[]}))
   ]);
   setPlantilla(Boolean(p.cargada));setRegistros(r.registros||[]);
  }
  setCargando(false);
 }
 useEffect(()=>{cargar().catch(e=>{setError(String(e));setCargando(false);});},[]);
 const docs=useMemo(()=>Object.entries(DOCUMENTOS).map(([id,d])=>({id,...d,faltan:datosCompletos(form,d.requeridos)})),[form]);
 const actual=docs.find(d=>d.id===hoja);
 const completos=docs.filter(d=>d.faltan.length===0).length;
 function actualiza(ref:string,valor:string){setForm(v=>({...v,[ref]:valor}));setConfirmado(false);setSeleccionado("");}
 async function entrar(e:React.FormEvent){
  e.preventDefault();setError("");setOcupado(true);
  try{await jsonSeguro(await fetch("/api/sesion",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({password:pass})}));setPass("");await cargar();}
  catch(e){setError((e as Error).message);}finally{setOcupado(false);}
 }
 async function subirPlantilla(archivo:File|null){
  if(!archivo)return;
  if(!archivo.name.toLowerCase().endsWith(".xlsx")){setError("Solo se admite la plantilla .xlsx");return;}
  setOcupado(true);setError("");setMensaje("");
  try{
   await upload("plantillas/alcanto.xlsx",archivo,{
    access:"private",handleUploadUrl:"/api/plantilla/upload",multipart:true,
    contentType:"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
   });
   await cargar();setMensaje("Plantilla privada cargada. El original no será modificado.");
  }catch(e){setError("Error al cargar plantilla: "+(e as Error).message);}
  finally{setOcupado(false);}
 }
 async function guardar(){
  setOcupado(true);setError("");setMensaje("");
  try{
   const r=await jsonSeguro(await fetch("/api/registros",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({datos:form})}));
   await cargar();setSeleccionado(r.registro.id);
   setMensaje("Trabajador guardado en almacenamiento privado. Ya puedes generar documentos.");
  }catch(e){setError((e as Error).message);}finally{setOcupado(false);}
 }
 async function seleccionar(id:string){
  if(!id){setSeleccionado("");setForm({});return;}
  setOcupado(true);setError("");
  try{
   const r=await jsonSeguro(await fetch("/api/registros/"+encodeURIComponent(id),{cache:"no-store"}));
   setForm(r.registro.datos);setSeleccionado(id);setSeccion("nuevo");setConfirmado(false);setMensaje("Registro cargado. Sus datos ya están disponibles.");
  }catch(e){setError((e as Error).message);}finally{setOcupado(false);}
 }
 async function imprimir(){
  setError("");setMensaje("");setOcupado(true);
  try{
   if(!seleccionado)throw new Error("Primero guarda el registro, o selecciona uno de la lista.");
   const res=await fetch("/api/impresion",{
    method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({id:seleccionado,hoja,confirmado})
   });
   if(!res.ok)await jsonSeguro(res);
   const blob=await res.blob();
   const url=URL.createObjectURL(blob);
   const a=document.createElement("a");a.href=url;a.download="ALCANTO_"+hoja.replace(/[^a-z0-9]/gi,"_")+".pdf";
   document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);
   setMensaje("PDF generado para revisar e imprimir. Conserva la documentación en lugar privado.");
  }catch(e){setError((e as Error).message);}finally{setOcupado(false);}
 }
 return <main className="shell">
  <header className="topbar"><div className="brand"><span className="mark">A</span><div><strong>ALCANTO</strong><small>Gestión documental de contratistas</small></div></div><span className="webtag">100% ONLINE · Sin Excel instalado</span></header>
  <div className="container">
   {cargando?<section className="panel">Cargando aplicación...</section>:!sesion?
    <section className="login panel">
     <div className="eyebrow">ACCESO PRIVADO</div>
     <h1>Tu documentación, desde cualquier lugar.</h1>
     <p>Administra empresas, trabajadores, contratos, IRL y prevención desde el navegador. El Excel original se conserva como plantilla de cálculo en un espacio privado.</p>
     {!instalado?<div className="notice warning">La aplicación requiere configurar su contraseña y secreto de sesión en Vercel antes del primer acceso.</div>:
      <form onSubmit={entrar} className="loginForm"><label>Contraseña de administración<input type="password" value={pass} onChange={e=>setPass(e.target.value)} minLength={12} autoComplete="current-password"/></label><button disabled={ocupado} className="primary">Ingresar</button></form>}
     {error&&<div className="notice err">{error}</div>}
     <p className="small">Por seguridad, no se guardan los RUT en el código público de GitHub.</p>
    </section>:
    <>
    <div className="heading"><div><div className="eyebrow">PANEL DE CONTROL</div><h1>Documentación de trabajadores</h1><p>Una sola ficha permite preparar los documentos vinculados a sus datos, respetando las fórmulas y formatos del XLSX original.</p></div>
    <button className="ghost" onClick={async()=>{await fetch("/api/sesion",{method:"DELETE"});setSesion(false);setRegistros([]);setForm({});}}>Cerrar sesión</button></div>
    {(error||mensaje)&&<div className={"notice "+(error?"err":"ok")}>{error||mensaje}<button className="x" onClick={()=>{setError("");setMensaje("");}}>×</button></div>}
    <div className="stats">
      <div className="stat"><small>Plantilla Excel privada</small><strong>{plantilla?"Configurada":"Pendiente"}</strong></div>
      <div className="stat"><small>Registros guardados</small><strong>{registros.length}</strong></div>
      <div className="stat"><small>Documentos con datos mínimos</small><strong>{completos} / 10</strong></div>
    </div>
    {(!almacenamiento||!motor||!plantilla)&&<section className="panel setup">
      <h2>Configuración inicial de la nube</h2>
      {!almacenamiento&&<p>1. Conectar el almacenamiento privado de Vercel Blob en el panel del proyecto.</p>}
      {!motor&&<p>2. Configurar las credenciales de Aspose.Cells Cloud para el cálculo y la conversión PDF.</p>}
      {almacenamiento&&!plantilla&&<div><p>3. Carga una sola vez tu plantilla original. Quedará almacenada de manera privada; no necesitas conservar el archivo en el computador para el uso diario.</p>
      <label className="upload">Seleccionar plantilla XLSX<input type="file" accept=".xlsx" disabled={ocupado} onChange={e=>subirPlantilla(e.target.files?.[0]||null)}/></label></div>}
    </section>}
    <div className="workspace">
     <nav className="sidebar panel"><strong>TRABAJADORES</strong><button className={seccion==="nuevo"?"current":""} onClick={()=>{setSeccion("nuevo");setSeleccionado("");setForm({});setConfirmado(false);}}>+ Nuevo registro</button>
      <div className="divider"/><span className="labelSmall">GUARDADOS</span>
      {registros.length?registros.map(r=><button key={r.id} className="worker" onClick={()=>seleccionar(r.id)} disabled={ocupado}><strong>{r.trabajador}</strong><span>{r.empresa}</span><small>{r.cargo||"Cargo pendiente"}</small></button>):<p className="small">Todavía no hay registros.</p>}
     </nav>
     <div className="column">
      <section className="panel formpanel"><div className="panelHead"><div><div className="eyebrow">PASO 1</div><h2>{seleccionado?"Ficha del trabajador":"Registrar empresa y trabajador"}</h2></div><span className="tag">{seleccionado?"REGISTRO GUARDADO":"NUEVA FICHA"}</span></div>
       <p className="small">Los campos marcados con su celda corresponden a entradas de tu Excel. Los campos calculados mediante fórmulas no se pueden editar aquí.</p>
       {grupos.map(([titulo,claves],i)=><details key={titulo} open={i===0||i===1}><summary>{titulo}</summary><div className="formgrid">{claves.map(ref=><label key={ref}>{CAMPOS[ref]} <small>{ref}</small><input value={form[ref]||""} onChange={e=>actualiza(ref,e.target.value)} inputMode={ref==="C32"?"numeric":"text"} maxLength={500}/></label>)}</div></details>)}
       <div className="actions"><button className="primary" onClick={guardar} disabled={ocupado||!almacenamiento||!form.C5||!form.C17||!form.C18}>Guardar como nuevo registro</button><span className="small">Los registros anteriores no se sobrescriben.</span></div>
      </section>
      <section className="panel"><div className="panelHead"><div><div className="eyebrow">PASO 2</div><h2>Documentación disponible</h2></div><span className="tag">{completos} con datos mínimos</span></div>
       <div className="docgrid">{docs.map(d=><div key={d.id} className="doc"><div className="docIcon">▤</div><div><strong>{d.nombre}</strong><small>{d.faltan.length?"Faltan "+d.faltan.length+" campos: "+d.faltan.join(", "):d.id==="PTS."?"Datos completos · verificar contenido PTS":"Datos mínimos completos · revisar documento"}</small></div></div>)}</div>
       <p className="small">«Datos mínimos completos» no acredita contenido preventivo validado, firmas o entrega efectiva.</p>
      </section>
      <section className="panel"><div className="eyebrow">PASO 3</div><h2>Documento PDF para imprimir</h2>
       <label>Tipo de documento<select value={hoja} onChange={e=>{setHoja(e.target.value);setConfirmado(false);}}>{Object.entries(DOCUMENTOS).map(([id,d])=><option value={id} key={id}>{d.nombre}</option>)}</select></label>
       {actual?.faltan.length? <div className="notice warning">Faltan campos de este documento: {actual.faltan.join(", ")}</div>:<p className="small">Disponible para revisión. El cálculo y el PDF se producen en la nube a partir de una copia temporal del libro.</p>}
       <label className="check"><input type="checkbox" checked={confirmado} onChange={e=>setConfirmado(e.target.checked)}/> Confirmo que revisaré la información, condiciones de prevención y firmas antes de utilizar el PDF.</label>
       <button className="primary" onClick={imprimir} disabled={ocupado||!seleccionado||!plantilla||!motor||!confirmado||!!actual?.faltan.length}>{ocupado?"Procesando...":"Generar PDF online"}</button>
       <p className="small">Esta conversión utiliza Aspose.Cells; la equivalencia visual con tu Excel debe validarse con documentos de prueba.</p>
      </section>
     </div>
    </div>
    </>
   }
   <footer>PROYECTO ALCANTO · Documentos privados · Fórmulas originales protegidas · Sistema de generación en la nube</footer>
  </div>
 </main>;
}
