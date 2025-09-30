export const metadata = { title: "AI Trading Dashboard" };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <body style={{ fontFamily: "system-ui, -apple-system, Segoe UI, Roboto" }}>
        <div style={{ maxWidth: 1000, margin: "24px auto", padding: "0 16px" }}>
          {children}
        </div>
      </body>
    </html>
  );
}
