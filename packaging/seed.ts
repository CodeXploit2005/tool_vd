import { db, pool } from "../desktop/keyzone-studio/src/db";
import { niches } from "../desktop/keyzone-studio/src/db/schema";
import { DEFAULT_NICHES } from "../desktop/keyzone-studio/scripts/default-niches";

async function main() {
  await db.insert(niches).values(DEFAULT_NICHES).onConflictDoNothing({ target: niches.slug });
  await pool.end();
}
main().catch(error => { console.error(error); process.exitCode = 1; });
