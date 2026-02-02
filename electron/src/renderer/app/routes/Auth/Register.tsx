/**
 * Register Page
 */
import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Lock, User, UserPlus, AlertCircle, CheckCircle } from 'lucide-react';
import { register } from '../../../lib/api/auth';

export const Register: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    display_name: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setError('Mật khẩu xác nhận không khớp');
      return;
    }

    // Validate password length
    if (formData.password.length < 6) {
      setError('Mật khẩu phải có ít nhất 6 ký tự');
      return;
    }

    setLoading(true);

    try {
      const result = await register({
        email: formData.email,
        password: formData.password,
        display_name: formData.display_name,
      });
      setSuccess(result.message);

      // Redirect to login after 2 seconds
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err: any) {
      setError(err.message || 'Đăng ký thất bại. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <h1 className="auth-logo">Minute</h1>
          <p className="auth-subtitle">AI-Powered Meeting Assistant</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <h2 className="auth-title">Tạo tài khoản</h2>

          {error && (
            <div className="auth-error">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="auth-success">
              <CheckCircle size={16} />
              <span>{success}</span>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="display_name">Họ và tên</label>
            <div className="input-with-icon">
              <User size={18} />
              <input
                id="display_name"
                name="display_name"
                type="text"
                placeholder="Nguyễn Văn A"
                value={formData.display_name}
                onChange={handleChange}
                required
                minLength={2}
                maxLength={100}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <div className="input-with-icon">
              <Mail size={18} />
              <input
                id="email"
                name="email"
                type="email"
                placeholder="your.email@company.com"
                value={formData.email}
                onChange={handleChange}
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
                name="password"
                type="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={handleChange}
                required
                minLength={6}
              />
            </div>
            <span className="input-hint">Ít nhất 6 ký tự</span>
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Xác nhận mật khẩu</label>
            <div className="input-with-icon">
              <Lock size={18} />
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                placeholder="••••••••"
                value={formData.confirmPassword}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={loading}
          >
            {loading ? (
              <span>Đang tạo tài khoản...</span>
            ) : (
              <>
                <UserPlus size={18} />
                <span>Đăng ký</span>
              </>
            )}
          </button>

          <div className="auth-footer">
            <p>
              Đã có tài khoản?{' '}
              <Link to="/login">Đăng nhập</Link>
            </p>
          </div>
        </form>
      </div>

      <style>{`
        .auth-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--bg-base);
          padding: var(--space-lg);
        }

        .auth-container {
          width: 100%;
          max-width: 420px;
        }

        .auth-header {
          text-align: center;
          margin-bottom: var(--space-xl);
        }

        .auth-logo {
          font-family: var(--font-heading);
          font-size: 2.5rem;
          font-weight: 700;
          color: var(--accent);
          margin: 0;
        }

        .auth-subtitle {
          color: var(--text-secondary);
          margin-top: var(--space-xs);
        }

        .auth-form {
          background: var(--bg-elevated);
          border: 1px solid var(--border);
          border-radius: var(--radius-lg);
          padding: var(--space-xl);
        }

        .auth-title {
          font-family: var(--font-heading);
          font-size: 1.5rem;
          font-weight: 600;
          color: var(--text-primary);
          margin: 0 0 var(--space-lg);
          text-align: center;
        }

        .auth-error {
          display: flex;
          align-items: center;
          gap: var(--space-xs);
          padding: var(--space-sm);
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.3);
          border-radius: var(--radius-sm);
          color: #ef4444;
          font-size: 0.875rem;
          margin-bottom: var(--space-md);
        }

        .auth-success {
          display: flex;
          align-items: center;
          gap: var(--space-xs);
          padding: var(--space-sm);
          background: rgba(34, 197, 94, 0.1);
          border: 1px solid rgba(34, 197, 94, 0.3);
          border-radius: var(--radius-sm);
          color: #22c55e;
          font-size: 0.875rem;
          margin-bottom: var(--space-md);
        }

        .form-group {
          margin-bottom: var(--space-md);
        }

        .form-group label {
          display: block;
          font-size: 0.875rem;
          font-weight: 500;
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

        .input-with-icon input,
        .input-with-icon select {
          width: 100%;
          padding: var(--space-sm) var(--space-sm) var(--space-sm) 2.5rem;
          background: var(--bg-surface);
          border: 1px solid var(--border);
          border-radius: var(--radius-sm);
          color: var(--text-primary);
          font-size: 1rem;
          transition: border-color 0.2s, box-shadow 0.2s;
        }

        .input-with-icon select {
          cursor: pointer;
          appearance: none;
        }

        .input-with-icon input:focus,
        .input-with-icon select:focus {
          outline: none;
          border-color: var(--accent);
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .input-with-icon input::placeholder {
          color: var(--text-secondary);
          opacity: 0.6;
        }

        .input-hint {
          display: block;
          font-size: 0.75rem;
          color: var(--text-secondary);
          margin-top: var(--space-xs);
        }

        .btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: var(--space-xs);
          padding: var(--space-sm) var(--space-md);
          border-radius: var(--radius-sm);
          font-size: 1rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
          border: none;
        }

        .btn-primary {
          background: var(--accent);
          color: white;
        }

        .btn-primary:hover:not(:disabled) {
          background: var(--accent-hover);
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
          font-weight: 500;
        }

        .auth-footer a:hover {
          text-decoration: underline;
        }
      `}</style>
    </div>
  );
};

export default Register;
