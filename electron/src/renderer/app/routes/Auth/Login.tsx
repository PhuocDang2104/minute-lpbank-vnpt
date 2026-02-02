/**
 * Login Page
 */
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Lock, LogIn, AlertCircle } from 'lucide-react';
import Vortex from '../../../components/ui/vortex';
import { login, getCurrentUser, storeUser } from '../../../lib/api/auth';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login({ email, password });
      const user = await getCurrentUser();
      storeUser(user);
      navigate('/app');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <Vortex
        containerClassName="auth-vortex"
        className="auth-vortex__content"
        particleCount={360}
        baseHue={30}
        baseSpeed={0.22}
        rangeSpeed={0.85}
        baseRadius={0.9}
        rangeRadius={2.2}
        backgroundColor="transparent"
      >
        <div className="auth-container">
          <div className="auth-card">
            <div className="auth-header">
              <Link to="/" className="auth-logo-link">
                <h1 className="auth-logo">Minute</h1>
              </Link>
              <p className="auth-subtitle">AI-Powered Meeting Assistant</p>
            </div>

            <form className="auth-form" onSubmit={handleSubmit}>
              <h2 className="auth-title">Đăng nhập</h2>

              {error && (
                <div className="auth-error">
                  <AlertCircle size={16} />
                  <span>{error}</span>
                </div>
              )}

              <div className="form-group">
                <label htmlFor="email">Email</label>
                <div className="input-with-icon">
                  <Mail size={18} />
                  <input
                    id="email"
                    type="email"
                    placeholder="your.email@company.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="password">Mật khẩu</label>
                <div className="input-with-icon">
                  <Lock size={18} />
                  <input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={6}
                  />
                </div>
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-block auth-btn"
                disabled={loading}
              >
                {loading ? (
                  <span>Đang đăng nhập...</span>
                ) : (
                  <>
                    <LogIn size={18} />
                    <span>Đăng nhập</span>
                  </>
                )}
              </button>

              <div className="auth-footer">
                <p>
                  Chưa có tài khoản?{' '}
                  <Link to="/register">Đăng ký ngay</Link>
                </p>
              </div>
            </form>

            <div className="auth-demo-info">
              <p><strong>Demo Account:</strong></p>
              <p>Email: vnpt@gmail.com</p>
              <p>Password: vnpt1234</p>
            </div>
          </div>
        </div>
      </Vortex>

      <style>{`
        .auth-page {
          min-height: 100vh;
          position: relative;
          background: radial-gradient(circle at top, rgba(247, 167, 69, 0.12), transparent 60%),
            #f8f6f0;
          overflow: hidden;
        }

        .auth-vortex {
          position: absolute;
          inset: 0;
        }

        .auth-vortex__content {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: var(--space-2xl) var(--space-lg);
        }

        .vortex-root {
          position: relative;
          width: 100%;
          height: 100%;
        }

        .vortex-canvas {
          position: absolute;
          inset: 0;
          pointer-events: none;
        }

        .vortex-canvas canvas {
          width: 100%;
          height: 100%;
          display: block;
        }

        .vortex-content {
          position: relative;
          z-index: 1;
          width: 100%;
          height: 100%;
        }

        .auth-container {
          width: min(520px, 90vw);
          margin: 0 auto;
          position: relative;
          z-index: 1;
        }

        .auth-card {
          position: relative;
          padding: var(--space-xl);
          background: rgba(255, 255, 255, 0.92);
          border: 1px solid rgba(0, 0, 0, 0.08);
          border-radius: 24px;
          box-shadow: 0 24px 60px rgba(15, 23, 42, 0.12);
          backdrop-filter: blur(10px);
        }

        .auth-card::after {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 4px;
          background: var(--cta-gradient);
          opacity: 0.7;
          border-top-left-radius: 24px;
          border-top-right-radius: 24px;
        }

        .auth-header {
          text-align: left;
          margin-bottom: var(--space-md);
        }

        .auth-logo-link {
          text-decoration: none;
        }

        .auth-logo {
          font-family: var(--font-heading);
          font-size: 2.4rem;
          font-weight: 700;
          margin: 0;
          background: var(--cta-gradient);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .auth-subtitle {
          color: var(--text-secondary);
          margin-top: var(--space-xs);
          font-size: 0.95rem;
        }

        .auth-form {
          background: rgba(255, 255, 255, 0.9);
          border: 1px solid var(--border-subtle);
          border-radius: 18px;
          padding: var(--space-md);
          box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
        }

        .auth-title {
          font-family: var(--font-heading);
          font-size: 1.25rem;
          font-weight: 600;
          color: var(--text-primary);
          margin: 0 0 var(--space-md);
          text-align: left;
        }

        .auth-error {
          display: flex;
          align-items: center;
          gap: var(--space-xs);
          padding: var(--space-sm);
          background: rgba(239, 68, 68, 0.12);
          border: 1px solid rgba(239, 68, 68, 0.3);
          border-radius: var(--radius-sm);
          color: #ef4444;
          font-size: 0.875rem;
          margin-bottom: var(--space-md);
        }

        .form-group {
          margin-bottom: var(--space-md);
        }

        .form-group label {
          display: block;
          font-size: 0.875rem;
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--space-xs);
        }

        .input-with-icon {
          position: relative;
          display: flex;
          align-items: center;
        }

        .input-with-icon svg {
          position: absolute;
          left: var(--space-sm);
          color: var(--text-secondary);
        }

        .input-with-icon input {
          width: 100%;
          padding: 12px var(--space-sm) 12px 2.6rem;
          background: rgba(255, 255, 255, 0.9);
          border: 1px solid rgba(0, 0, 0, 0.1);
          border-radius: 12px;
          color: var(--text-primary);
          font-size: 0.95rem;
          transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
        }

        .input-with-icon input:focus {
          outline: none;
          border-color: rgba(247, 167, 69, 0.6);
          background: #ffffff;
          box-shadow: 0 0 0 3px rgba(247, 167, 69, 0.18);
        }

        .input-with-icon input::placeholder {
          color: var(--text-secondary);
          opacity: 0.6;
        }

        .btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: var(--space-xs);
          padding: var(--space-sm) var(--space-md);
          border-radius: 999px;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
          border: none;
        }

        .btn-primary {
          background: var(--accent);
          color: var(--text-on-accent);
        }

        .auth-btn {
          background: var(--cta-gradient);
          border: 1px solid rgba(247, 167, 69, 0.6);
          box-shadow: 0 16px 32px rgba(247, 167, 69, 0.35);
          transform: translateZ(0);
        }

        .auth-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 22px 40px rgba(247, 167, 69, 0.45);
        }

        .btn-primary:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn-block {
          width: 100%;
          margin-top: var(--space-md);
        }

        .auth-footer {
          margin-top: var(--space-lg);
          text-align: center;
          color: var(--text-secondary);
          font-size: 0.875rem;
        }

        .auth-footer a {
          color: var(--accent);
          text-decoration: none;
          font-weight: 600;
        }

        .auth-footer a:hover {
          text-decoration: underline;
        }

        .auth-demo-info {
          margin-top: var(--space-md);
          padding: var(--space-md);
          background: rgba(255, 255, 255, 0.7);
          border: 1px dashed rgba(0, 0, 0, 0.12);
          border-radius: 14px;
          font-size: 0.75rem;
          color: var(--text-secondary);
          text-align: center;
        }

        .auth-demo-info p {
          margin: var(--space-xs) 0;
        }

        @media (max-width: 640px) {
          .auth-page {
            padding: 0;
          }

          .auth-vortex__content {
            padding: var(--space-xl) var(--space-md);
          }

          .auth-card {
            padding: var(--space-lg);
          }

          .auth-form {
            padding: var(--space-md);
          }
        }

        @media (prefers-reduced-motion: reduce) {
          .auth-vortex canvas {
            display: none;
          }

          .auth-btn {
            transition: none;
          }
        }
      `}</style>
    </div>
  );
};

export default Login;

