import { randomBytes } from 'node:crypto';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { createRequire } from 'node:module';
import { createLicenseServer } from '../../license-server/server.mjs';

const require = createRequire(import.meta.url);
const password = process.env.KEYZONE_DEV_PASSWORD || randomBytes(12).toString('base64url');
const server = createLicenseServer({
  database: ':memory:',
  password,
  publicUrl: 'http://localhost:4317',
});
server.listen(0, '127.0.0.1');
await once(server, 'listening');
console.log('Local admin: http://localhost:4317/admin');
if (!process.env.KEYZONE_DEV_PASSWORD) console.log('Local admin password:', password);
const next = spawn(process.execPath, [
  require.resolve('next/dist/bin/next'), 'dev', '--hostname', '127.0.0.1', '--port', '4317', ...process.argv.slice(2),
], {
  stdio: 'inherit',
  env: { ...process.env, KEYZONE_DEV_BACKEND: 'http://127.0.0.1:' + server.address().port },
});
next.on('exit', code => { server.close(); process.exitCode = code ?? 1; });
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => next.kill());
