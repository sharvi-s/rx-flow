import React, { useState } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_API_URL;

function Login({ onLogin }) {
  const [isRegister, setIsRegister] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'pharmacist' });
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const endpoint = isRegister ? '/api/auth/register' : '/api/auth/login';
      const payload = isRegister ? form : { email: form.email, password: form.password };
      const res = await axios.post(`${API}${endpoint}`, payload);
      localStorage.setItem('user', JSON.stringify(res.data.user));
      onLogin(res.data.token);
    } catch (err) {
      setError(err.response?.data?.message || 'Something went wrong');
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.logo}>💊 RxFlow</div>
        <h2 style={styles.title}>{isRegister ? 'Create Account' : 'Welcome Back'}</h2>
        <p style={styles.subtitle}>Pharmacy Claims Management</p>

        {error && <div style={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit}>
          {isRegister && (
            <input
              placeholder="Full Name"
              value={form.name}
              onChange={e => setForm({...form, name: e.target.value})}
              required
            />
          )}
          <input
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={e => setForm({...form, email: e.target.value})}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={form.password}
            onChange={e => setForm({...form, password: e.target.value})}
            required
          />
          {isRegister && (
            <select value={form.role} onChange={e => setForm({...form, role: e.target.value})}>
              <option value="pharmacist">Pharmacist</option>
              <option value="technician">Technician</option>
              <option value="manager">Manager</option>
            </select>
          )}
          <button type="submit" style={styles.btn}>
            {isRegister ? 'Register' : 'Login'}
          </button>
        </form>

        <p style={styles.toggle}>
          {isRegister ? 'Already have an account?' : "Don't have an account?"}
          <span style={styles.link} onClick={() => setIsRegister(!isRegister)}>
            {isRegister ? ' Login' : ' Register'}
          </span>
        </p>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh', display: 'flex',
    alignItems: 'center', justifyContent: 'center',
    background: 'linear-gradient(135deg, #4361ee 0%, #3a0ca3 100%)'
  },
  card: {
    background: 'white', borderRadius: '16px',
    padding: '40px', width: '100%', maxWidth: '420px',
    boxShadow: '0 20px 60px rgba(0,0,0,0.2)'
  },
  logo: { fontSize: '32px', textAlign: 'center', marginBottom: '8px' },
  title: { fontSize: '24px', fontWeight: '700', textAlign: 'center', color: '#1a1a2e' },
  subtitle: { color: '#666', textAlign: 'center', marginBottom: '24px', fontSize: '14px' },
  error: {
    background: '#fee2e2', color: '#dc2626',
    padding: '10px', borderRadius: '6px',
    marginBottom: '16px', fontSize: '14px'
  },
  btn: {
    width: '100%', padding: '12px',
    background: 'linear-gradient(135deg, #4361ee, #3a0ca3)',
    color: 'white', fontSize: '16px',
    borderRadius: '8px', marginTop: '4px'
  },
  toggle: { textAlign: 'center', marginTop: '20px', fontSize: '14px', color: '#666' },
  link: { color: '#4361ee', fontWeight: '600', cursor: 'pointer' }
};

export default Login;