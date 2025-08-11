import React, { useState } from 'react';
import './LoginForm.css';

interface LoginFormProps {
  onLogin: (password: string) => void;
  isLoading: boolean;
  error?: string;
}

const LoginForm: React.FC<LoginFormProps> = ({ onLogin, isLoading, error }) => {
  const [password, setPassword] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (password.trim()) {
      onLogin(password);
    }
  };

  return (
    <div className="login-overlay">
      <div className="login-form">
        <div className="login-header">
          <h1>🔒 Lost Valley Image Management</h1>
          <p>Enter password to continue</p>
        </div>
        
        <form onSubmit={handleSubmit}>
          <input
            type="password"
            placeholder="Enter password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="password-input"
            disabled={isLoading}
            autoFocus
          />
          
          {error && <div className="error-message">{error}</div>}
          
          <button 
            type="submit" 
            className="login-button"
            disabled={isLoading || !password.trim()}
          >
            {isLoading ? 'Checking...' : 'Access Site'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginForm;