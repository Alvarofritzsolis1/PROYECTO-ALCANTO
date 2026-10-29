export const CAMPOS: Record<string, string> = {
  C5: "Nombre o razón social", C6: "RUT empresa", C7: "Representante legal",
  C8: "RUT representante", C9: "Teléfono empresa", C10: "Domicilio empresa",
  C11: "Comuna empresa", C12: "Ciudad empresa", C13: "Correo empresa", C14: "Rubro empresa",
  C17: "Nombre completo trabajador", C18: "RUT trabajador", C19: "Nacionalidad",
  C21: "Estado civil", C22: "Domicilio trabajador", C23: "Comuna trabajador",
  C24: "Ciudad trabajador", C25: "Correo trabajador", C26: "Teléfono trabajador",
  C29: "Cargo o especialidad", D30: "Obra / faena (código según catálogo original)",
  C31: "Jornada semanal", C32: "Sueldo base (pesos, solo números)", C34: "Frecuencia de pago",
  C35: "Datos de pago", C38: "AFP", C39: "Salud", C43: "Obras autorizadas para traslado",
  C44: "Asignación de locomoción",
};
export const DOCUMENTOS: Record<string,{nombre:string;requeridos:string[]}> = {
  "Contrato Imprimible": { nombre: "Contrato de trabajo", requeridos: ["C5","C6","C7","C8","C17","C18","C29","D30","C31","C32","C34","C38","C39"] },
  "Anexo Traslado": { nombre: "Anexo de traslado", requeridos: ["C5","C6","C17","C18","C29","D30","C43"] },
  "Anexo extension contrato": { nombre: "Prórroga de contrato", requeridos: ["C5","C6","C7","C8","C17","C18"] },
  "INDUCCION PREVENCION": { nombre: "Inducción de prevención", requeridos: ["C5","C6","C7","C8","D30"] },
  "IRL": { nombre: "Información de riesgos laborales", requeridos: ["C5","C6","C17","C18","C29","D30"] },
  "PTS.": { nombre: "Procedimiento de trabajo seguro", requeridos: ["C5","C6","C7","C8","C29"] },
  "ENTREGA PTS": { nombre: "Entrega de PTS", requeridos: ["C5","C6","C17","C18","C29"] },
  "Registros Entrega EPP": { nombre: "Entrega de EPP", requeridos: ["C5","C6","C17","C18","C29","D30"] },
  "REGLAMENTO INTERNO": { nombre: "Recepción reglamento interno", requeridos: ["C5","C6","C17","C18"] },
  "DECLARACION JURADA": { nombre: "Declaración jurada", requeridos: ["C5","C6","C7","C8","D30"] },
};
export function validarDatos(value: unknown): Record<string,string> {
 if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("Datos no válidos");
 const resultado:Record<string,string>={};
 for(const [clave,valor] of Object.entries(value)){
   if(!(clave in CAMPOS)) throw new Error("Campo no autorizado: "+clave);
   if(typeof valor !== "string" || valor.length > 500) throw new Error("Valor de "+clave+" incorrecto");
   const limpio=valor.trim();
   if(!limpio) continue;
   if(clave==="C32" && !/^\d{1,12}$/.test(limpio))throw new Error("Sueldo debe ser numérico");
   resultado[clave]=limpio;
 }
 return resultado;
}
