"use client"

import { useEffect, useState } from "react"

const apiBase = process.env.NEXT_PUBLIC_API_BASE

function statusBadge(status) {
  const map = {
    up_to_date: "bg-emerald-600",
    updates: "bg-amber-600",
    security: "bg-red-600",
    reboot: "bg-indigo-600",
    offline: "bg-slate-600"
  }
  return map[status] || "bg-slate-600"
}

export default function HomePage() {
  const [servers, setServers] = useState([])
  const [filter, setFilter] = useState("")

  useEffect(() => {
    const token = localStorage.getItem("token")
    if (!token) {
      window.location.href = "/login"
      return
    }
    fetch(`${apiBase}/api/servers`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then((res) => res.json())
      .then(setServers)
  }, [])

  const filtered = servers.filter((srv) => srv.hostname.toLowerCase().includes(filter.toLowerCase()))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Servers</h1>
        <input placeholder="Search hostname" value={filter} onChange={(e) => setFilter(e.target.value)} />
      </div>
      <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
        <table>
          <thead>
            <tr className="text-slate-400">
              <th>Hostname</th>
              <th>IP</th>
              <th>OS</th>
              <th>Last Seen</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((srv) => (
              <tr key={srv.id} className="hover:bg-slate-900">
                <td>
                  <a className="text-blue-400" href={`/servers/${srv.id}`}>
                    {srv.hostname}
                  </a>
                </td>
                <td>{srv.ip}</td>
                <td>
                  {srv.os_name} {srv.os_version}
                </td>
                <td>{srv.last_seen || "Never"}</td>
                <td>
                  <span className={`rounded-full px-3 py-1 text-xs ${statusBadge(srv.status)}`}>{srv.status}</span>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={5} className="py-6 text-center text-slate-400">
                  No servers yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
