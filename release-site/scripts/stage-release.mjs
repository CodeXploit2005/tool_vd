import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';

const [platform, metadataPath] = process.argv.slice(2);
if (!['windows', 'android'].includes(platform) || !metadataPath) {
  throw Error('Usage: node scripts/stage-release.mjs windows|android path/to/release.json');
}
const publicDir = fileURLToPath(new URL('../public/', import.meta.url));
const manifestPath = path.join(publicDir, 'release-' + platform + '.json');
const current = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
if (path.basename(metadata.filename) !== metadata.filename ||
    !metadata.filename.endsWith(platform === 'windows' ? '.exe' : '.apk')) throw Error('Invalid installer name');
const installer = fs.readFileSync(path.join(path.dirname(metadataPath), metadata.filename));
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
if (digest(installer) !== metadata.sha256 || installer.length !== metadata.bytes) throw Error('Installer checksum mismatch');
const parts = [];
const partSize = 8 * 1024 * 1024;
fs.mkdirSync(path.join(publicDir, 'downloads', platform), {recursive: true});
for (let offset = 0; offset < installer.length; offset += partSize) {
  const chunk = installer.subarray(offset, offset + partSize);
  const part = 'downloads/' + platform + '/part-' + String(parts.length).padStart(3, '0') + '.bin';
  fs.writeFileSync(path.join(publicDir, part), chunk);
  parts.push({path: part, bytes: chunk.length, sha256: digest(chunk)});
}
fs.writeFileSync(manifestPath, JSON.stringify({...current, ...metadata, parts}, null, 2) + '\n');
console.log(platform, metadata.version, parts.length, 'parts verified and staged');
