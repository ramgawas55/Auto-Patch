"use client"

import { useState } from "react"

const apiBase = process.env.NEXT_PUBLIC_API_BASE

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")

  const submit = async (e) => {
    e.preventDefault()
    setError("")
    const body = new URLSearchParams()
    body.append("username", email)
    body.append("password", password)
    const res = await fetch(`${apiBase}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body
    })
    if (!res.ok) {
      setError("Invalid credentials")
      return
    }
    const data = await res.json()
    localStorage.setItem("token", data.access_token)
    window.location.href = "/"
  }

  return (
    <div className="mx-auto max-w-md rounded-xl border border-slate-800 bg-slate-950 p-8">
      <h1 className="mb-6 text-2xl font-semibold">Sign in</h1>
      <form onSubmit={submit} className="space-y-4">
        <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
        {error && <div className="text-sm text-red-400">{error}</div>}
        <button type="submit" className="w-full">
          Login
        </button>
      </form>
    </div>
  )
}
