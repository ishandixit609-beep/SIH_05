/** Skeleton while a page loads; if a request keeps failing it says so and offers a retry instead of waiting forever. */
export function Loading({ label, apis }: { label: string; apis: { err: Error | null; reload: () => void }[] }) {
  const bad = apis.find(a => a.err)
  if (bad) return (
    <div className="card loaderr" role="alert"><h4>{label} did not load</h4>
      <p className="sm dim">{bad.err!.message || 'The mock API did not answer.'} If you just restarted the dev server, hard-reload once (Cmd+Shift+R) so the mock service worker takes over the page.</p>
      <button className="btn dark" onClick={() => apis.forEach(a => a.reload())}>Try again</button></div>
  )
  return (
    <div className="skel" aria-busy="true" aria-label={label}><div className="t xs dim up">{label}</div>
      <div className="skrow"><i /><i /><i /></div><div className="skrow big"><i /><i /></div></div>
  )
}
