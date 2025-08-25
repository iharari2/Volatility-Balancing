export const metadata = { title: "VB MVP", description: "Volatility Balancing" };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (<html lang="en"><body style={{fontFamily:"Inter, sans-serif", padding:16}}>{children}</body></html>);
}
