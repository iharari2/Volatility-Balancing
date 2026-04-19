import { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

interface PasswordInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  inputStyle?: React.CSSProperties;
}

export default function PasswordInput({ inputStyle, className, style, ...props }: PasswordInputProps) {
  const [show, setShow] = useState(false);

  const isDark = !!inputStyle;

  return (
    <div style={{ position: 'relative', display: 'block', ...style }}>
      <input
        {...props}
        type={show ? 'text' : 'password'}
        className={className}
        style={inputStyle ? { ...inputStyle, paddingRight: 40 } : undefined}
      />
      <button
        type="button"
        tabIndex={-1}
        aria-label={show ? 'Hide password' : 'Show password'}
        onClick={() => setShow((s) => !s)}
        style={{
          position: 'absolute',
          right: 10,
          top: '50%',
          transform: 'translateY(-50%)',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: 0,
          display: 'flex',
          alignItems: 'center',
          color: isDark ? '#64748b' : '#9ca3af',
        }}
      >
        {show ? <EyeOff size={15} /> : <Eye size={15} />}
      </button>
    </div>
  );
}
