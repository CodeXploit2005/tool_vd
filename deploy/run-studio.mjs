import { spawn } from "node:child_process";
import { mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { bootstrap } from "./bootstrap.mjs";

const studio = fileURLToPath(new URL("../moonreel/moonreel-studio/", import.meta.url));
if (!process.env.MUSE2API_BASE_URL && process.env.MUSE2API_INTERNAL_HOSTPORT) process.env.MUSE2API_BASE_URL = `http://${process.env.MUSE2API_INTERNAL_HOSTPORT}`;
if (process.env.RENDER && (!process.env.STUDIO_ACCESS_USER || !process.env.STUDIO_ACCESS_PASSWORD)) throw new Error("Configure STUDIO_ACCESS_USER and STUDIO_ACCESS_PASSWORD before exposing the Studio");
for (const directory of [process.env.STORAGE_DIR,process.env.NICHES_DIR]) if(directory) await mkdir(directory,{recursive:true});
await bootstrap(studio);
const children=[];
let stopping=false;
function start(label,args) {
  const child=spawn(process.execPath,args,{cwd:studio,env:process.env,stdio:"inherit",detached:process.platform!=="win32"});
  children.push(child);
  child.on("error",()=>shutdown(1));
  child.on("exit",code=>{if(!stopping){console.error(`[supervisor] ${label} stopped (${code}); restarting service`);void shutdown(1);}});
}
async function shutdown(code) {
  if(stopping)return;
  stopping=true;
  const exits=children.map(child=>new Promise(resolve=>{if(child.exitCode!==null||child.signalCode!==null)resolve();else {child.once("exit",resolve);child.kill("SIGTERM");}}));
  const timer=setTimeout(()=>{for(const child of children){try{process.platform!=="win32"?process.kill(-child.pid,"SIGKILL"):child.kill("SIGKILL");}catch{}}process.exit(code);},240_000);
  await Promise.all(exits);clearTimeout(timer);process.exit(code);
}
process.on("SIGTERM",()=>void shutdown(0));process.on("SIGINT",()=>void shutdown(0));
start("worker",["node_modules/tsx/dist/cli.mjs","src/worker/index.ts"]);
start("web",["node_modules/next/dist/bin/next","start","--hostname","0.0.0.0","--port",process.env.PORT||"10000"]);
