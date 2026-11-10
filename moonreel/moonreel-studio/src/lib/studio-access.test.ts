import assert from "node:assert/strict";
import test from "node:test";
import { studioAccess } from "./studio-access";
const auth=(value:string)=>`Basic ${Buffer.from(value).toString("base64")}`;
test("public deployment guard protects API and pages with configured credentials",()=>{
  assert.equal(studioAccess(null,"admin","test:password"),"denied");
  assert.equal(studioAccess(auth("admin:test:password"),"admin","test:password"),"allowed");
  assert.equal(studioAccess(auth("wrong:test:password"),"admin","test:password"),"denied");
  assert.equal(studioAccess(auth("admin:wrong"),"admin","test:password"),"denied");
  assert.equal(studioAccess("Basic invalid","admin","test:password"),"denied");
  assert.equal(studioAccess(null,"admin",undefined),"misconfigured");
  assert.equal(studioAccess(null,undefined,undefined),"allowed");
});
