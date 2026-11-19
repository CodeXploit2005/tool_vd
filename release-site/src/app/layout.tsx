import type { Metadata, Viewport } from "next";
import Script from "next/script";
import "./globals.css";
import { Ambient3DBackground } from "@/components/Ambient3DBackground";
import { HydrationComplete } from "@/components/HydrationComplete";

export const metadata: Metadata = {
  title: "KeyZone Video Studio — Windows & Android",
  description:
    "Tải KeyZone Video Studio cho Windows và Android. Viết kịch bản, tạo nhân vật xuyên suốt, dựng và xuất video ngay trên thiết bị của bạn.",
  icons: {
    icon: "./keyzone-icon.png",
  },
};

export const viewport: Viewport = {
  themeColor: "#0c0821",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" className="dark">
      <body className="relative isolate min-h-screen selection:bg-fuchsia-500/30 selection:text-fuchsia-100">
        {process.env.NODE_ENV === "development" && (
          <Script id="normalize-extension-markers" strategy="beforeInteractive">
            {`(() => {
              const marker = 'bis_skin_checked';
              function cleanTree(root) {
                root.removeAttribute(marker);
                root.querySelectorAll('[bis_skin_checked]').forEach(el => el.removeAttribute(marker));
              }
              function cleanBody() {
                const body = document.body;
                if (!body) return;
                body.removeAttribute('bis_register');
                for (const name of body.getAttributeNames()) {
                  if (/^__processed_[0-9a-f-]{36}__$/i.test(name)) body.removeAttribute(name);
                }
              }
              const observer = new MutationObserver(records => {
                for (const record of records) {
                  if (record.type === 'attributes') {
                    if (record.attributeName === marker) record.target.removeAttribute(marker);
                    else if (record.target === document.body) cleanBody();
                  } else {
                    for (const node of record.addedNodes) {
                      if (node.nodeType === 1) cleanTree(node);
                    }
                  }
                }
              });
              observer.observe(document.documentElement, { subtree: true, childList: true, attributes: true });
              window.addEventListener('keyzone:hydrated', () => observer.disconnect(), { once: true });
              cleanTree(document.documentElement);
              cleanBody();
            })()`}
          </Script>
        )}
        <Ambient3DBackground />
        <div className="relative z-10">{children}</div>
        {process.env.NODE_ENV === "development" && <HydrationComplete />}
      </body>
    </html>
  );
}
