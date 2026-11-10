import { createRequire } from "node:module";
import { readFile } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import path from "node:path";

export async function bootstrap(studio) {
  if(!process.env.DATABASE_URL)throw new Error("DATABASE_URL is required");
  const require=createRequire(path.join(studio,"package.json"));
  const {Client}=require("pg");
  const client=new Client({connectionString:process.env.DATABASE_URL,connectionTimeoutMillis:10_000});
  await client.connect();
  try {
    await client.query("BEGIN");
    await client.query("SELECT pg_advisory_xact_lock(746201105)");
    const {rows:[tables]}=await client.query("SELECT to_regclass('public.projects') AS projects,to_regclass('public.niches') AS niches");
    if(!tables.projects&&!tables.niches) {
      await client.query(await readFile(new URL("./initial-schema.sql",import.meta.url),"utf8"));
      console.log("[bootstrap] Initialized fresh database");
    } else if(!tables.projects||!tables.niches) throw new Error("Partially initialized database: restore or review schema before starting");
    await client.query("ALTER TABLE projects ADD COLUMN IF NOT EXISTS script_source text NOT NULL DEFAULT 'generated'");
    await client.query("ALTER TABLE projects ADD COLUMN IF NOT EXISTS reference_image_kind text NOT NULL DEFAULT 'place'");
    await client.query("ALTER TABLE projects ADD COLUMN IF NOT EXISTS product_image_paths jsonb NOT NULL DEFAULT '[]'::jsonb");
    await client.query("COMMIT");
  } catch(error) {await client.query("ROLLBACK");throw error;} finally {await client.end();}
  const seed=spawnSync(process.execPath,["node_modules/tsx/dist/cli.mjs","scripts/seed.ts"],{cwd:studio,env:process.env,stdio:"inherit"});
  if(seed.status!==0)throw new Error("Database seeding failed");
}
