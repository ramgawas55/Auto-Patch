import "./globals.css"

export const metadata = {
  title: process.env.NEXT_PUBLIC_APP_NAME || "AutoPatch"
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen">
          <header className="border-b border-slate-800 bg-slate-950">
            <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
              <div className="text-lg font-semibold">AutoPatch</div>
              <nav className="flex gap-4 text-sm text-slate-300">
                <a href="/">Servers</a>
                <a href="/approvals">Approvals</a>
                <a href="/settings">Settings</a>
              </nav>
            </div>
          </header>
          <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
        </div>
      </body>
    </html>
  )
}
