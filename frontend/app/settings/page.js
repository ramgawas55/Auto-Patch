"use client"

import { useState } from "react"

const apiBase = process.env.NEXT_PUBLIC_API_BASE

export default function SettingsPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [role, setRole] = useState("operator")
  const [message, setMessage] = useState("")

  const submit = async () => {
    const token = localStorage.getItem("token")
    if (!token) {
      window.location.href = "/login"
      return
    }
    const res = await fetch(`${apiBase}/api/users`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, role })
    })
    if (res.ok) {
      setMessage("User created")
    } else {
      setMessage("Failed to create user")
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
        <h2 className="mb-4 text-lg font-semibold">Create User</h2>
        <div className="grid grid-cols-2 gap-4">
          <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <select value={role} onChange={(e) => setRole(e.target.value)}>
            <option value="operator">Operator</option>
            <option value="admin">Admin</option>
          </select>
          <button onClick={submit}>Create</button>
        </div>
        {message && <div className="mt-3 text-sm text-slate-300">{message}</div>}
      </div>
      <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
        <h2 className="mb-4 text-lg font-semibold">Rotate Agent Token</h2>
        <RotateToken />
      </div>
    </div>
  )
}

function RotateToken() {
  const [serverId, setServerId] = useState("")
  const [result, setResult] = useState("")

  const rotate = async () => {
    const token = localStorage.getItem("token")
    if (!token) {
      window.location.href = "/login"
      return
    }
    const res = await fetch(`${apiBase}/api/servers/${serverId}/rotate-token`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` }
    })
    if (res.ok) {
      const data = await res.json()
      setResult(`New token: ${data.agent_token}`)
    } else {
      setResult("Rotation failed")
    }
  }

  return (
    <div className="flex items-center gap-3">
      <input placeholder="Server ID" value={serverId} onChange={(e) => setServerId(e.target.value)} />
      <button onClick={rotate}>Rotate</button>
      {result && <span className="text-sm text-slate-300">{result}</span>}
    </div>
  )
}
