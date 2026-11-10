import { NextResponse, type NextRequest } from "next/server";
import { LOCALE_COOKIE, resolveLocale } from "@/i18n/config";
import { studioAccess } from "@/lib/studio-access";

export function proxy(request: NextRequest) {
  if(request.nextUrl.pathname==="/api/ready")return NextResponse.next();
  const access=studioAccess(request.headers.get("authorization"),process.env.STUDIO_ACCESS_USER,process.env.STUDIO_ACCESS_PASSWORD);
  if(access==="misconfigured")return new NextResponse("Studio access is not configured",{status:503});
  if(access!=="allowed")return new NextResponse("Studio sign-in required",{status:401,headers:{"WWW-Authenticate":'Basic realm="KeyZone Studio", charset="UTF-8"',"Cache-Control":"no-store"}});
  if(request.nextUrl.pathname.startsWith("/api/")||/\.[^/]+$/.test(request.nextUrl.pathname))return NextResponse.next();
  const locale=resolveLocale(request.cookies.get(LOCALE_COOKIE)?.value,request.headers.get("accept-language"));
  const url=request.nextUrl.clone();url.pathname=`/${locale}${url.pathname==="/"?"":url.pathname}`;
  return NextResponse.rewrite(url);
}
export const config={matcher:["/((?!_next/static|_next/image).*)"]};
