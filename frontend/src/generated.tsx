// frontend/src/pages/Dashboard.tsx
import { useEffect, useState } from 'react';
import { Card, Button, Spinner, EmptyState, Badge } from '../components/ui';
import { tokens } from '../theme/tokens';

interface Project {
  id: string;
  name: string;
  description: string;
  status: 'draft' | 'in_progress' | 'completed' | 'failed';
  updatedAt: string;
  stage: string;
}

export function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/projects', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      if (!res.ok) throw new Error('Failed to load projects');
      const data = await res.json();
      setProjects(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const statusColor = (status: Project['status']) => {
    switch (status) {
      case 'completed': return tokens.colors.success;
      case 'in_progress': return tokens.colors.primary;
      case 'failed': return tokens.colors.error;
      default: return tokens.colors.muted;
    }
  };

  if (loading) {
    return (
      <div style={{ padding: tokens.space[6], display: 'flex', flexDirection: 'column', gap: tokens.space[4] }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 style={{ fontSize: tokens.fontSizes['2xl'], fontWeight: tokens.fontWeights.bold, color: tokens.colors.text }}>oiioii</h1>
          <Button variant="primary" disabled><Spinner size="sm" /></Button>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: tokens.space[4] }}>
          {[1, 2, 3].map(i => (
            <Card key={i} style={{ minHeight: 200 }}>
              <div style={{ height: 24, background: tokens.colors.muted, borderRadius: tokens.radii.md, marginBottom: tokens.space[3] }} />
              <div style={{ height: 16, background: tokens.colors.muted, borderRadius: tokens.radii.sm, width: '60%', marginBottom: tokens.space[2] }} />
              <div style={{ height: 16, background: tokens.colors.muted, borderRadius: tokens.radii.sm, width: '40%' }} />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: tokens.space[6], display: 'flex', flexDirection: 'column', gap: tokens.space[4], alignItems: 'center', textAlign: 'center' }}>
        <h1 style={{ fontSize: tokens.fontSizes['2xl'], fontWeight: tokens.fontWeights.bold, color: tokens.colors.text }}>oiioii</h1>
        <EmptyState
          title="Failed to load projects"
          description={error}
          actionLabel="Retry"
          onAction={fetchProjects}
        />
      </div>
    );
  }

  return (
    <div style={{ padding: tokens.space[6], display: 'flex', flexDirection: 'column', gap: tokens.space[6] }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: tokens.space[3] }}>
        <h1 style={{ fontSize: tokens.fontSizes['2xl'], fontWeight: tokens.fontWeights.bold, color: tokens.colors.text }}>oiioii</h1>
        <Button variant="primary" onClick={() => window.location.href = '/projects/new'}>
          New Project
        </Button>
      </div>

      {projects.length === 0 ? (
        <EmptyState
          title="No projects yet"
          description="Create your first AI animation project to start the creative workflow."
          actionLabel="New Project"
          onAction={() => window.location.href = '/projects/new'}
        />
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: tokens.space[4] }}>
          {projects.map(p => (
            <Card key={p.id} style={{ display: 'flex', flexDirection: 'column', gap: tokens.space[3] }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h3 style={{ fontSize: tokens.fontSizes.lg, fontWeight: tokens.fontWeights.semibold, color: tokens.colors.text }}>{p.name}</h3>
                  <p style={{ fontSize: tokens.fontSizes.sm, color: tokens.colors.muted, marginTop: tokens.space[1] }}>{p.description}</p>
                </div>
                <Badge style={{ background: statusColor(p.status), color: tokens.colors.background }}>{p.status.replace('_', ' ')}</Badge>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: tokens.fontSizes.xs, color: tokens.colors.muted }}>
                <span>Stage: {p.stage}</span>
                <span>Updated: {new Date(p.updatedAt).toLocaleDateString()}</span>
              </div>
              <Button variant="secondary" size="sm" onClick={() => window.location.href = `/projects/${p.id}`}>
                Open Workspace
              </Button>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
```

```tsx
// frontend/src/pages/Login.tsx
import { useState } from 'react';
import { Card, Button, Input, Spinner } from '../components/ui';
import { tokens } from '../theme/tokens';

export function Login({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Login failed');
      localStorage.setItem('token', data.access_token);
      onLogin();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: tokens.space[6],
      background: tokens.colors.background,
    }}>
      <Card style={{ width: '100%', maxWidth: 400, padding: tokens.space[6] }}>
        <div style={{ textAlign: 'center', marginBottom: tokens.space[6] }}>
          <h1 style={{ fontSize: tokens.fontSizes['2xl'], fontWeight: tokens.fontWeights.bold, color: tokens.colors.text }}>oiioii</h1>
          <p style={{ color: tokens.colors.muted, marginTop: tokens.space[2] }}>Sign in to your animation workspace</p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: tokens.space[4] }}>
          {error && (
            <div style={{
              padding: tokens.space[3],
              background: `${tokens.colors.error}15`,
              border: `1px solid ${tokens.colors.error}`,
              borderRadius: tokens.radii.md,
              color: tokens.colors.error,
              fontSize: tokens.fontSizes.sm,
            }}>
              {error}
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: tokens.space[1] }}>
            <label style={{ fontSize: tokens.fontSizes.sm, fontWeight: tokens.fontWeights.medium, color: tokens.colors.text }}>Email</label>
            <Input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              disabled={loading}
              required
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: tokens.space[1] }}>
            <label style={{ fontSize: tokens.fontSizes.sm, fontWeight: tokens.fontWeights.medium, color: tokens.colors.text }}>Password</label>
            <Input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              disabled={loading}
              required
            />
          </div>

          <Button type="submit" variant="primary" disabled={loading} style={{ marginTop: tokens.space[2] }}>
            {loading ? <Spinner size="sm" /> : 'Sign In'}
          </Button>
        </form>

        <p style={{ textAlign: 'center', marginTop: tokens.space[4], fontSize: tokens.fontSizes.sm, color: tokens.colors.muted }}>
          Don't have an account?{' '}
          <a href="/register" style={{ color: tokens.colors.primary, fontWeight: tokens.fontWeights.medium, textDecoration: 'none' }}>
            Register
          </a>
        </p>
      </Card>
    </div>
  );
}
```

```tsx
// frontend/src/App.tsx
import { useEffect, useState } from 'react';
import { Dashboard } from './pages/Dashboard';
import { Login } from './pages/Login';
import { tokens } from '../theme/tokens';

export function App() {
  const [authed, setAuthed] = useState<boolean | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    setAuthed(!!token);
  }, []);

  if (authed === null) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: tokens.colors.background,
      }}>
        <div style={{ fontSize: tokens.fontSizes.lg, color: tokens.colors.muted }}>Loading…</div>
      </div>
    );
  }

  return authed ? (
    <Dashboard />
  ) : (
    <Login onLogin={() => setAuthed(true)} />
  );
}