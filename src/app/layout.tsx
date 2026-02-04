import type { Metadata } from "next";
import { Inter } from "next/font/google";
import cn from "classnames";

import "./globals.css";

const inter = Inter({ subsets: ["latin"] });
const isProd = process.env.NODE_ENV === 'production';
const basePath = isProd ? '/staticdex' : '';

export const metadata: Metadata = {
  title: "StaticDex",
  description: "Static version of Seadex.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="icon" href={`${basePath}/favicon/favicon.png`} />
        <meta name="theme-color" content="#000" />
      </head>
      <body className={cn(inter.className, "bg-slate-950 text-slate-100")}>
        <div className="min-h-screen">{children}</div>
      </body>
    </html>
  );
}
