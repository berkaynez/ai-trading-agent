import "./globals.css";

export const metadata = { title: "AI Trading Dashboard" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <body>
        <div className="container">{children}</div>
      </body>
    </html>
  );
}