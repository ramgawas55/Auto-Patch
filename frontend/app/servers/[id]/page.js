"use client"

import { useEffect, useState } from "react"

const apiBase = process.env.NEXT_PUBLIC_API_BASE

export default function ServerDetail({ params }) {
  const [inventory, setInventory] = useState(null)
  const [updates, setUpdates] = useState([])
  const [jobs, setJobs] = useState([])
  const [logs, setLogs] = useState("")
  const [selectedJobId, setSelectedJobId] = useState(null)
  const [securityOnly, setSecurityOnly] = useState(false)
  const [jobType, setJobType] = useState("SCAN_NOW")
  const [scheduledAt, setScheduledAt] = useState("")
  const [requiresApproval, setRequiresApproval] = useState(true)
  const [message, setMessage] = useState("")

  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null

  useEffect(() => {
    if (!token) {
      window.location.href = "/login"
      return
    }
    fetch(`${apiBase}/api/servers/${params.id}/inventory`, { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => res.json())
      .then(setInventory)
    fetch(`${apiBase}/api/servers/${params.id}/updates`, { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => res.json())
      .then(setUpdates)
    fetch(`${apiBase}/api/servers/${params.id}/jobs`, { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => res.json())
      .then(setJobs)
  }, [params.id])

  const loadLogs = async (jobId) => {
    if (!token) return
    setSelectedJobId(jobId)
    const res = await fetch(`${apiBase}/api/jobs/${jobId}/results`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (res.ok) {
      const data = await res.json()
      const merged = data
        .map((item) => `Status: ${item.status}\nExit: ${item.exit_code}\nStdout:\n${item.stdout || ""}\nStderr:\n${item.stderr || ""}`)
        .join("\n\n")
      setLogs(merged || "No logs")
    } else {
      setLogs("Failed to load logs")
    }
  }

  const submitJob = async () => {
    if (!token) return
    setMessage("")
    const payload = {
      server_id: Number(params.id),
      job_type: jobType,
      scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : null,
      requires_approval: requiresApproval
    }
    const res = await fetch(`${apiBase}/api/jobs`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
    if (res.ok) {
      setMessage("Job created")
      const data = await res.json()
      setJobs((prev) => [data, ...prev])
    } else {
      setMessage("Failed to create job")
    }
  }

  const filteredUpdates = securityOnly ? updates.filter((update) => update.is_security) : updates

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Server Detail</h1>
        <a className="text-blue-400" href="/">
          Back to servers
        </a>
      </div>
      <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
        {inventory ? (
          <div className="grid grid-cols-2 gap-4 text-sm text-slate-300">
            <div>Hostname: {inventory.hostname}</div>
            <div>IP: {inventory.ip}</div>
            <div>OS: {inventory.os_name} {inventory.os_version}</div>
            <div>Kernel: {inventory.kernel_version}</div>
            <div>Package Manager: {inventory.package_manager}</div>
            <div>Reboot Required: {inventory.reboot_required ? "Yes" : "No"}</div>
            <div>Security Updates: {inventory.security_updates_count}</div>
            <div>Updates: {inventory.updates_count}</div>
          </div>
        ) : (
          <div className="text-slate-400">No inventory yet</div>
        )}
      </div>
      <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
        <h2 className="mb-4 text-lg font-semibold">Create Job</h2>
        <div className="grid grid-cols-2 gap-4">
          <select value={jobType} onChange={(e) => setJobType(e.target.value)}>
            <option value="SCAN_NOW">SCAN_NOW</option>
            <option value="APPLY_PATCHES">APPLY_PATCHES</option>
            <option value="APPLY_SECURITY_ONLY">APPLY_SECURITY_ONLY</option>
            <option value="REPORT_ONLY">REPORT_ONLY</option>
            <option value="REBOOT">REBOOT</option>
          </select>
          <input type="datetime-local" value={scheduledAt} onChange={(e) => setScheduledAt(e.target.value)} />
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={requiresApproval} onChange={(e) => setRequiresApproval(e.target.checked)} />
            Require approval
          </label>
          <button onClick={submitJob}>Create Job</button>
        </div>
        {message && <div className="mt-3 text-sm text-slate-300">{message}</div>}
      </div>
      <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
        <h2 className="mb-4 text-lg font-semibold">Available Updates</h2>
        <label className="mb-3 flex items-center gap-2 text-sm text-slate-300">
          <input type="checkbox" checked={securityOnly} onChange={(e) => setSecurityOnly(e.target.checked)} />
          Security only
        </label>
        <table>
          <thead>
            <tr className="text-slate-400">
              <th>Package</th>
              <th>Current</th>
              <th>Candidate</th>
              <th>Security</th>
            </tr>
          </thead>
          <tbody>
            {filteredUpdates.map((update) => (
              <tr key={update.id}>
                <td>{update.name}</td>
                <td>{update.current_version || "-"}</td>
                <td>{update.candidate_version || "-"}</td>
                <td>{update.is_security ? "Yes" : "No"}</td>
              </tr>
            ))}
            {filteredUpdates.length === 0 && (
              <tr>
                <td colSpan={4} className="py-4 text-center text-slate-400">
                  No updates
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
        <h2 className="mb-4 text-lg font-semibold">Job History</h2>
        <table>
          <thead>
            <tr className="text-slate-400">
              <th>Type</th>
              <th>Status</th>
              <th>Created</th>
              <th>Logs</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr key={job.id}>
                <td>{job.job_type}</td>
                <td>{job.status}</td>
                <td>{job.created_at}</td>
                <td>
                  <button className="bg-slate-700" onClick={() => loadLogs(job.id)}>
                    View
                  </button>
                </td>
              </tr>
            ))}
            {jobs.length === 0 && (
              <tr>
                <td colSpan={4} className="py-4 text-center text-slate-400">
                  No jobs yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
        {selectedJobId && (
          <div className="mt-4 rounded-lg border border-slate-800 bg-slate-900 p-3 text-sm text-slate-200">
            <div className="mb-2 text-slate-400">Job {selectedJobId} Logs</div>
            <pre className="whitespace-pre-wrap">{logs}</pre>
          </div>
        )}
      </div>
    </div>
  )
}
