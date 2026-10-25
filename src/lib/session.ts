// Demo-only sign-in. Nothing is sent anywhere; the "account" lives in this browser.
export interface User { name: string; email: string; role: 'Scrutiny officer' | 'Institution' | 'Auditor' }
const K = 'satyapan-user'
export const getUser = (): User | null => { try { const s = localStorage.getItem(K); return s ? JSON.parse(s) : null } catch { return null } }
export const setUser = (u: User | null) => { try { u ? localStorage.setItem(K, JSON.stringify(u)) : localStorage.removeItem(K) } catch { /* private mode */ } }
