import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PROYECTO ALCANTO | Gestión de contratistas",
  description: "Documentación laboral y prevención online con las fórmulas del Excel original",
  robots: { index: false, follow: false },
};
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="es"><body>{children}</body></html>;
}
