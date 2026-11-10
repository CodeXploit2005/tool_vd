import { pool } from "@/db";
export async function GET() {
  try {await pool.query("SELECT 1");return Response.json({ok:true},{headers:{"Cache-Control":"no-store"}});}
  catch {return Response.json({ok:false},{status:503,headers:{"Cache-Control":"no-store"}});}
}
