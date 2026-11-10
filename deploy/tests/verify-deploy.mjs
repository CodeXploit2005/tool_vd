// Local-only integration test: creates and drops only its own uniquely named empty database.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { spawn } from "node:child_process";
import { bootstrap } from "../bootstrap.mjs";
const studio=fileURLToPath(new URL("../../moonreel/moonreel-studio/",import.meta.url));
const require=createRequire(path.join(studio,"package.json"));const {Client}=require("pg");
const source=new URL(process.env.DATABASE_URL);
assert.ok(["localhost","127.0.0.1","[::1]"].includes(source.hostname),"This probe is restricted to local PostgreSQL");
const name=`codex_publish_probe_${randomUUID().replaceAll("-","")}`;
assert.match(name,/^codex_publish_probe_[a-f0-9]{32}$/);
const admin=new Client({connectionString:source.href});await admin.connect();
let created=false,server;
try {
  await admin.query(`CREATE DATABASE "${name}"`);created=true;
  source.pathname=`/${name}`;process.env.DATABASE_URL=source.href;
  process.env.NICHES_DIR=path.join(studio,".probe-empty-niches",name);process.env.MUSE2API_KEY="probe-only";process.env.STUDIO_ACCESS_USER="probe";process.env.STUDIO_ACCESS_PASSWORD=randomUUID();
  await bootstrap(studio);await bootstrap(studio);
  const db=new Client({connectionString:source.href});await db.connect();
  try {
    const {rows:[row]}=await db.query("SELECT count(*)::int count FROM niches");assert.ok(row.count>0);
    await db.query("SELECT script_source,reference_image_kind,product_image_paths FROM projects LIMIT 0");
  } finally {await db.end();}
  console.log("PASS: baseline initializes fresh database; bootstrap and seeding are idempotent");
  const port=32173;
  server=spawn(process.execPath,["node_modules/next/dist/bin/next","start","--hostname","0.0.0.0","--port",String(port)],{cwd:studio,env:process.env,stdio:["ignore","pipe","pipe"]});
  let errors="";server.stderr.on("data",chunk=>errors+=chunk);server.stdout.resume();
  const base=`http://localhost:${port}`;
  let ready=false;
  for(let i=0;i<80;i++){try{if((await fetch(`${base}/api/ready`)).status===200){ready=true;break;}}catch{}await new Promise(resolve=>setTimeout(resolve,250));}
  assert.ok(ready,`Probe web not ready: ${errors.slice(-500)}`);
  for(const route of ["/accounts","/api/muse-connect","/api/files/unknown.jpg"])assert.equal((await fetch(base+route)).status,401,route);
  const authorization=`Basic ${Buffer.from(`probe:${process.env.STUDIO_ACCESS_PASSWORD}`).toString("base64")}`;
  const home=await fetch(base+"/",{headers:{authorization}});assert.equal(home.status,200,errors.slice(-4000));
  console.log("PASS: public readiness, protected API/media/pages and authenticated UI HTTP 200");
} finally {
  if(server&&server.exitCode===null){server.kill("SIGTERM");await Promise.race([new Promise(resolve=>server.once("exit",resolve)),new Promise(resolve=>setTimeout(resolve,5000))]);if(server.exitCode===null)server.kill("SIGKILL");}
  if(created)await admin.query(`DROP DATABASE "${name}" WITH (FORCE)`);
  await admin.end();console.log("Removed only the dedicated deployment probe database");
}
