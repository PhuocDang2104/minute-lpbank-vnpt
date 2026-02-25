import { FormEvent, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useAuth } from '../../context/AuthContext';
import { useLocaleText } from '../../i18n/useLocaleText';
import { login, register as registerUser } from '../../lib/api/auth';
import { ApiError } from '../../lib/apiClient';

const getErrorMessage = (error: unknown, fallback: string): string => {
  if (error instanceof ApiError) {
    const payload = error.data;
    if (payload && typeof payload === 'object' && 'detail' in payload) {
      const detail = (payload as { detail?: unknown }).detail;
      if (typeof detail === 'string' && detail.trim()) {
        return detail;
      }
    }
  }
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }
  return fallback;
};

const Register = () => {
  const { refreshUser, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const { lt } = useLocaleText();

  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/app/meetings', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError(lt('Mật khẩu xác nhận không khớp.', 'Password confirmation does not match.'));
      return;
    }
    if (password.length < 6) {
      setError(lt('Mật khẩu phải có ít nhất 6 ký tự.', 'Password must be at least 6 characters.'));
      return;
    }

    setIsSubmitting(true);
    try {
      const normalizedEmail = email.trim().toLowerCase();
      await registerUser({
        email: normalizedEmail,
        password,
        display_name: displayName.trim(),
      });
      await login({ email: normalizedEmail, password });
      await refreshUser();
      navigate('/app/meetings', { replace: true });
    } catch (err) {
      setError(getErrorMessage(err, lt('Đăng ký thất bại.', 'Registration failed.')));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <img src="/minute_icon.svg" alt="Minute" className="auth-brand__logo" />
          <div>
            <h1>{lt('Đăng ký tài khoản', 'Create account')}</h1>
            <p>{lt('Bắt đầu sử dụng Minute cho họp tiếng Việt', 'Start using Minute for Vietnamese meetings')}</p>
          </div>
        </div>

        {error && <div className="form-error">{error}</div>}

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">{lt('Tên hiển thị', 'Display name')}</label>
            <input
              type="text"
              className="form-input"
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
              placeholder={lt('Ví dụ: Nguyễn Văn A', 'Example: John Doe')}
              autoComplete="name"
              minLength={2}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">{lt('Email', 'Email')}</label>
            <input
              type="email"
              className="form-input"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="name@company.com"
              autoComplete="email"
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">{lt('Mật khẩu', 'Password')}</label>
            <input
              type="password"
              className="form-input"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="••••••••"
              autoComplete="new-password"
              minLength={6}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">{lt('Xác nhận mật khẩu', 'Confirm password')}</label>
            <input
              type="password"
              className="form-input"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              placeholder="••••••••"
              autoComplete="new-password"
              minLength={6}
              required
            />
          </div>
          <button className="btn btn--primary auth-submit" type="submit" disabled={isSubmitting}>
            {isSubmitting ? lt('Đang tạo tài khoản...', 'Creating account...') : lt('Đăng ký', 'Register')}
          </button>
        </form>

        <p className="auth-footer">
          {lt('Đã có tài khoản?', 'Already have an account?')}{' '}
          <Link to="/login">{lt('Đăng nhập', 'Login')}</Link>
        </p>
      </div>
    </div>
  );
};

export default Register;
