import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";

test("disk-backed Render services do not set unsupported shutdown delay",async()=>{
  const yaml=await readFile(new URL("../../render.yaml",import.meta.url),"utf8");
  const services=yaml.split(/^  - type: /m).slice(1);
  assert.ok(services.length>=2);
  for(const service of services) {
    if(/^    disk:/m.test(service))assert.ok(!/^    maxShutdownDelaySeconds:/m.test(service),"Render rejects custom shutdown delay with a persistent disk");
  }
});
