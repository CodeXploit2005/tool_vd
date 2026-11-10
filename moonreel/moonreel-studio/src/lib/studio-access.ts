import { createHash, timingSafeEqual } from "node:crypto";
const digest=(value:string)=>createHash("sha256").update(value).digest();
export function studioAccess(header:string|null,user:string|undefined,password:string|undefined):"allowed"|"denied"|"misconfigured" {
  if(!user&&!password)return "allowed";
  if(!user||!password)return "misconfigured";
  if(!header?.startsWith("Basic "))return "denied";
  try {
    const value=Buffer.from(header.slice(6),"base64").toString("utf8");const colon=value.indexOf(":");
    if(colon<0)return "denied";
    const validUser=timingSafeEqual(digest(value.slice(0,colon)),digest(user));
    const validPassword=timingSafeEqual(digest(value.slice(colon+1)),digest(password));
    return validUser&&validPassword?"allowed":"denied";
  } catch {return "denied";}
}
