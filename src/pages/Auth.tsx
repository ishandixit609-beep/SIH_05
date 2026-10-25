import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { setUser, type User } from '../lib/session'

const ROLES: User['role'][] = ['Scrutiny officer', 'Institution', 'Auditor']
/** Demo sign-in / sign-up. No server, no password is stored or sent: it only sets who is shown in the header. */
export function AuthPage() {
  const nav = useNavigate(); const [mode, setMode] = useState<'in' | 'up'>('in'); const [role, setRole] = useState<User['role']>('Scrutiny officer')
  const [name, setName] = useState(''); const [email, setEmail] = useState(''); const [pw, setPw] = useState(''); const [err, setErr] = useState('')
  const submit = () => {
    if (!/^\S+@\S+\.\S+$/.test(email)) return setErr('Enter a valid email address.')
    if (pw.length < 6) return setErr('Use at least 6 characters.')
    if (mode === 'up' && name.trim().length < 2) return setErr('Enter your name.')
    setUser({ name: name.trim() || email.split('@')[0], email, role }); nav('/')
  }
  return (
    <div className="authwrap">
      <aside className="authside">
        <div className="brand"><span className="word" style={{ fontSize: '1.3rem' }}>SATYAPAN</span><span className="dv" lang="hi" style={{ textAlign: 'left' }}>सत्यापन</span></div>
        <div><h1>Every flag leads back to a page of proof.</h1>
          <ul style={{ padding: 0, listStyle: 'none', marginTop: 22 }}><li>✓ Evidence box on the exact PDF page</li><li>✓ Approve is blocked until checks pass or are waived</li><li>✓ Every act sealed into a hash chain</li></ul></div>
        <div className="t xs" style={{ color: '#8FA4C6' }}>SYNTHETIC DATA · DEMO ACCOUNTS ONLY</div>
      </aside>
      <div className="authform"><div className="authcard card">
        <div className="seg2" role="tablist"><button className={mode === 'in' ? 'on' : ''} onClick={() => setMode('in')}>Sign in</button><button className={mode === 'up' ? 'on' : ''} onClick={() => setMode('up')}>Create account</button></div>
        {mode === 'up' && <><label htmlFor="nm">Full name</label><input id="nm" type="text" value={name} onChange={e => setName(e.target.value)} /></>}
        <label htmlFor="em">Official email</label><input id="em" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="name@aicte-india.org" />
        <label htmlFor="pw">Password</label><input id="pw" type="password" value={pw} onChange={e => setPw(e.target.value)} onKeyDown={e => e.key === 'Enter' && submit()} />
        <label>I am a</label><div className="roles">{ROLES.map(r => <button key={r} className={role === r ? 'on' : ''} onClick={() => setRole(r)}>{r}</button>)}</div>
        {err && <div className="err" role="alert" style={{ marginTop: 10 }}>{err}</div>}
        <button className="act info" style={{ marginTop: 18 }} onClick={submit}>{mode === 'in' ? 'Sign in' : 'Create account'}</button>
        <p className="xs dim" style={{ marginTop: 12 }}>Demo only: nothing is sent or stored on a server. <Link to="/">Skip and open the docket →</Link></p>
      </div></div>
    </div>
  )
}
