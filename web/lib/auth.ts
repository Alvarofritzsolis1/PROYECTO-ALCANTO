import { createHmac, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";

const COOKIE = "alcanto_sesion";
const TTL = 12 * 60 * 60 * 1000;

function secreto() {
 const s=process.env.ALCANTO_SESSION_SECRET;
 if(!s || s.length<32) return null;
 return s;
}
export function configurado() {
 return Boolean(secreto() && process.env.ALCANTO_PASSWORD && process.env.ALCANTO_PASSWORD.length >= 12);
}
function firma(payload:string, secret:string) {
 return createHmac("sha256",secret).update(payload).digest("hex");
}
export async function iniciarSesion(password: string): Promise<boolean> {
 const expected=process.env.ALCANTO_PASSWORD;
 const secret=secreto();
 if(!expected || !secret || expected.length < 12 || typeof password !=="string") return false;
 const a=createHmac("sha256",secret).update(password).digest();
 const b=createHmac("sha256",secret).update(expected).digest();
 if(!timingSafeEqual(a,b))return false;
 const payload=String(Date.now()+TTL);
 const token=payload+"."+firma(payload,secret);
 (await cookies()).set(COOKIE,token,{
   httpOnly:true,secure:process.env.NODE_ENV==="production",sameSite:"strict",path:"/",maxAge:TTL/1000
 });
 return true;
}
export async function autorizado():Promise<boolean> {
 const secret=secreto();
 if(!secret)return false;
 const token=(await cookies()).get(COOKIE)?.value || "";
 const [timestamp,signature]=token.split(".");
 if(!timestamp||!signature|| !/^\d{13}$/.test(timestamp) || !/^[0-9a-f]{64}$/.test(signature)) return false;
 const ts=Number(timestamp);
 if(ts<Date.now() || ts>Date.now()+TTL) return false;
 return timingSafeEqual(Buffer.from(signature,"hex"),Buffer.from(firma(timestamp,secret),"hex"));
}
export async function cerrarSesion() { (await cookies()).delete(COOKIE); }
export function denegado() {
 return Response.json({error:"Debes iniciar sesión."},{status:401,headers:{"Cache-Control":"no-store"}});
}
