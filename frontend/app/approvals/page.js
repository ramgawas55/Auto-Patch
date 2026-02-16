"use client"

import { useEffect, useState } from "react"

const apiBase = process.env.NEXT_PUBLIC_API_BASE

export default function ApprovalsPage() {
  const [items, setItems] = useState([])
  const [message, setMessage] = useState("")
  const [reasons, setReasons] = useState({})

  useEffect(() => {
    const token = localStorage.getItem("token")
    if (!token) {
      window.location.href = "/login"
      return
    }
    fetch(`${apiBase}/api/approvals`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then((res) => res.json())
      .then(setItems)
  }, [])

  const act = async (jobId, action) => {
    const token = localStorage.getItem("token")
    if (!token) return
    const res = await fetch(`${apiBase}/api/approvals/${jobId}/${action}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ reason: reasons[jobId] || "" })
    })
    if (res.ok) {
      setMessage(`Job ${action}d`)
      setItems((prev) => prev.filter((item) => item.id !== jobId))
    } else {
      setMessage("Action failed")
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Approvals</h1>
      {message && <div className="text-sm text-slate-300">{message}</div>}
      <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
        <table>
          <thead>
            <tr className="text-slate-400">
              <th>Job</th>
              <th>Server</th>
              <th>Created</th>
              <th>Reason</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {items.map((job) => (
              <tr key={job.id}>
                <td>{job.job_type}</td>
                <td>{job.server_id}</td>
                <td>{job.created_at}</td>
                <td>
                  <input
                    placeholder="Reason"
                    value={reasons[job.id] || ""}
                    onChange={(e) => setReasons((prev) => ({ ...prev, [job.id]: e.target.value }))}
                  />
                </td>
                <td className="space-x-2">
                  <button onClick={() => act(job.id, "approve")}>Approve</button>
                  <button className="bg-slate-700" onClick={() => act(job.id, "deny")}>
                    Deny
                  </button>
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={5} className="py-4 text-center text-slate-400">
                  No approvals pending
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
