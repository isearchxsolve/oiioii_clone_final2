import React, { forwardRef, useState, type ButtonHTMLAttributes, type InputHTMLAttributes, type HTMLAttributes } from 'react';
import { tokens } from '../../theme/tokens';

// Helper to merge class names
function cx(...classes: (string | undefined | null | false)[]) {
  return classes.filter(Boolean).join(' ');
}

// Button
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', loading, disabled, children, className, onMouseEnter, onMouseLeave, onFocus, onBlur, ...props }, ref) => {
    const [isHovered, setIsHovered] = useState(false);
    const [isFocused, setIsFocused] = useState(false);

    const baseStyles: React.CSSProperties = {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: tokens.spacing[2],
      fontWeight: tokens.fontWeight.medium,
      borderRadius: tokens.borderRadius.md,
      transition: 'all 150ms ease',
      cursor: disabled || loading ? 'not-allowed' : 'pointer',
      opacity: disabled || loading ? 0.6 : 1,
      border: 'none',
      outline: 'none',
    };

    const sizeStyles: Record<string, React.CSSProperties> = {
      sm: { padding: `${tokens.spacing[1]} ${tokens.spacing[3]}`, fontSize: tokens.fontSize.sm, height: tokens.sizing[8] },
      md: { padding: `${tokens.spacing[2]} ${tokens.spacing[4]}`, fontSize: tokens.fontSize.base, height: tokens.sizing[10] },
      lg: { padding: `${tokens.spacing[3]} ${tokens.spacing[6]}`, fontSize: tokens.fontSize.lg, height: tokens.sizing[12] },
    };

    const variantStyles: Record<string, React.CSSProperties> = {
      primary: {
        backgroundColor: tokens.color.primary[600],
        color: tokens.color.white,
        boxShadow: `0 1px 2px 0 ${tokens.color.primary[600]}40`,
      },
      secondary: {
        backgroundColor: tokens.color.gray[100],
        color: tokens.color.gray[900],
        border: `1px solid ${tokens.color.gray[300]}`,
      },
      ghost: {
        backgroundColor: 'transparent',
        color: tokens.color.primary[600],
      },
      danger: {
        backgroundColor: tokens.color.danger[600],
        color: tokens.color.white,
        boxShadow: `0 1px 2px 0 ${tokens.color.danger[600]}40`,
      },
    };

    const hoverStyles: Record<string, React.CSSProperties> = {
      primary: { backgroundColor: tokens.color.primary[700] },
      secondary: { backgroundColor: tokens.color.gray[200] },
      ghost: { backgroundColor: tokens.color.primary[50] },
      danger: { backgroundColor: tokens.color.danger[700] },
    };

    const focusRing: React.CSSProperties = {
      boxShadow: `0 0 0 3px ${tokens.color.primary[200]}`,
    };

    const style = {
      ...baseStyles,
      ...sizeStyles[size],
      ...variantStyles[variant],
      ...(isHovered && !disabled && !loading ? hoverStyles[variant] : {}),
      ...(isFocused && !disabled && !loading ? focusRing : {}),
    } as React.CSSProperties;

    return (
      <button
        ref={ref}
        className={cx(className)}
        style={style}
        disabled={disabled || loading}
        onMouseEnter={(e) => {
          setIsHovered(true);
          onMouseEnter?.(e);
        }}
        onMouseLeave={(e) => {
          setIsHovered(false);
          onMouseLeave?.(e);
        }}
        onFocus={(e) => {
          setIsFocused(true);
          onFocus?.(e);
        }}
        onBlur={(e) => {
          setIsFocused(false);
          onBlur?.(e);
        }}
        {...props}
      >
        {loading && (
          <svg
            className="animate-spin h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {children}
      </button>
    );
  }
);
Button.displayName = 'Button';

// Input
interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, className, id, onFocus, onBlur, ...props }, ref) => {
    const [isFocused, setIsFocused] = useState(false);
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');

    const baseStyles: React.CSSProperties = {
      width: '100%',
      padding: `${tokens.spacing[2]} ${tokens.spacing[3]}`,
      fontSize: tokens.fontSize.base,
      lineHeight: tokens.lineHeight.normal,
      color: tokens.color.gray[900],
      backgroundColor: tokens.color.white,
      border: `1px solid ${tokens.color.gray[300]}`,
      borderRadius: tokens.borderRadius.md,
      transition: 'border-color 150ms ease, box-shadow 150ms ease',
      outline: 'none',
    };

    const focusStyles: React.CSSProperties = {
      borderColor: tokens.color.primary[500],
      boxShadow: `0 0 0 3px ${tokens.color.primary[100]}`,
    };

    const errorStyles: React.CSSProperties = {
      borderColor: tokens.color.danger[500],
      boxShadow: `0 0 0 3px ${tokens.color.danger[100]}`,
    };

    const disabledStyles: React.CSSProperties = {
      backgroundColor: tokens.color.gray[100],
      color: tokens.color.gray[500],
      cursor: 'not-allowed',
    };

    const style = {
      ...baseStyles,
      ...(props.disabled ? disabledStyles : {}),
      ...(error ? errorStyles : isFocused ? focusStyles : {}),
    } as React.CSSProperties;

    return (
      <div className={cx(className)} style={{ width: '100%' }}>
        {label && (
          <label
            htmlFor={inputId}
            style={{
              display: 'block',
              marginBottom: tokens.spacing[1],
              fontSize: tokens.fontSize.sm,
              fontWeight: tokens.fontWeight.medium,
              color: tokens.color.gray[700],
            }}
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          style={style}
          onFocus={(e) => {
            setIsFocused(true);
            onFocus?.(e);
          }}
          onBlur={(e) => {
            setIsFocused(false);
            onBlur?.(e);
          }}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined}
          {...props}
        />
        {error && (
          <p id={`${inputId}-error`} style={{ marginTop: tokens.spacing[1], fontSize: tokens.fontSize.sm, color: tokens.color.danger[600] }}>
            {error}
          </p>
        )}
        {helperText && !error && (
          <p id={`${inputId}-helper`} style={{ marginTop: tokens.spacing[1], fontSize: tokens.fontSize.sm, color: tokens.color.gray[500] }}>
            {helperText}
          </p>
        )}
      </div>
    );
  }
);
Input.displayName = 'Input';

// Card
interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'outlined' | 'elevated';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ variant = 'default', padding = 'md', className, children, ...props }, ref) => {
    const variantStyles: Record<string, React.CSSProperties> = {
      default: {
        backgroundColor: tokens.color.white,
        border: `1px solid ${tokens.color.gray[200]}`,
      },
      outlined: {
        backgroundColor: tokens.color.white,
        border: `1px solid ${tokens.color.gray[300]}`,
      },
      elevated: {
        backgroundColor: tokens.color.white,
        boxShadow: tokens.shadow.lg,
        border: 'none',
      },
    };

    const paddingStyles: Record<string, React.CSSProperties> = {
      none: {},
      sm: { padding: tokens.spacing[3] },
      md: { padding: tokens.spacing[4] },
      lg: { padding: tokens.spacing[6] },
    };

    const style = {
      borderRadius: tokens.borderRadius.lg,
      ...variantStyles[variant],
      ...paddingStyles[padding],
    } as React.CSSProperties;

    return (
      <div ref={ref} className={cx(className)} style={style} {...props}>
        {children}
      </div>
    );
  }
);
Card.displayName = 'Card';

// Badge
interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'sm' | 'md';
  dot?: boolean;
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ variant = 'default', size = 'md', dot, className, children, ...props }, ref) => {
    const variantStyles: Record<string, React.CSSProperties> = {
      default: { backgroundColor: tokens.color.gray[100], color: tokens.color.gray[700] },
      success: { backgroundColor: tokens.color.success[100], color: tokens.color.success[700] },
      warning: { backgroundColor: tokens.color.warning[100], color: tokens.color.warning[700] },
      danger: { backgroundColor: tokens.color.danger[100], color: tokens.color.danger[700] },
      info: { backgroundColor: tokens.color.info[100], color: tokens.color.info[700] },
    };

    const sizeStyles: Record<string, React.CSSProperties> = {
      sm: { padding: `${tokens.spacing[0.5]} ${tokens.spacing[1.5]}`, fontSize: tokens.fontSize.xs, borderRadius: tokens.borderRadius.full },
      md: { padding: `${tokens.spacing[1]} ${tokens.spacing[2]}`, fontSize: tokens.fontSize.sm, borderRadius: tokens.borderRadius.full },
    };

    const style = {
      display: 'inline-flex',
      alignItems: 'center',
      gap: tokens.spacing[1],
      fontWeight: tokens.fontWeight.medium,
      lineHeight: 1,
      ...variantStyles[variant],
      ...sizeStyles[size],
    } as React.CSSProperties;

    return (
      <span ref={ref} className={cx(className)} style={style} {...props}>
        {dot && (
          <span
            style={{
              width: size === 'sm' ? tokens.sizing[1.5] : tokens.sizing[2],
              height: size === 'sm' ? tokens.sizing[1.5] : tokens.sizing[2],
              borderRadius: '50%',
              backgroundColor: 'currentColor',
              flexShrink: 0,
            }}
            aria-hidden="true"
          />
        )}
        {children}
      </span>
    );
  }
);
Badge.displayName = 'Badge';

// Spinner
interface SpinnerProps extends HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg';
  color?: 'primary' | 'white' | 'current';
}

export const Spinner = forwardRef<HTMLDivElement, SpinnerProps>(
  ({ size = 'md', color = 'primary', className, ...props }, ref) => {
    const sizeMap = { sm: tokens.sizing[4], md: tokens.sizing[8], lg: tokens.sizing[12] };
    const colorMap = {
      primary: tokens.color.primary[600],
      white: tokens.color.white,
      current: 'currentColor',
    };

    const style: React.CSSProperties = {
      width: sizeMap[size],
      height: sizeMap[size],
      border: `2px solid ${colorMap[color]}40`,
      borderTopColor: colorMap[color],
      borderRadius: '50%',
      animation: 'spin 0.6s linear infinite',
    };

    return (
      <div
        ref={ref}
        className={cx(className)}
        style={style}
        role="status"
        aria-label="Loading"
        {...props}
      >
        <style jsx global>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }
);
Spinner.displayName = 'Spinner';

// EmptyState
interface EmptyStateProps extends HTMLAttributes<HTMLDivElement> {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export const EmptyState = forwardRef<HTMLDivElement, EmptyStateProps>(
  ({ icon, title, description, action, className, ...props }, ref) => {
    const containerStyle: React.CSSProperties = {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      textAlign: 'center',
      padding: tokens.spacing[10],
      gap: tokens.spacing[4],
    };

    const iconStyle: React.CSSProperties = {
      width: tokens.sizing[16],
      height: tokens.sizing[16],
      color: tokens.color.gray[400],
      flexShrink: 0,
    };

    const titleStyle: React.CSSProperties = {
      margin: 0,
      fontSize: tokens.fontSize.lg,
      fontWeight: tokens.fontWeight.semibold,
      color: tokens.color.gray[900],
    };

    const descriptionStyle: React.CSSProperties = {
      margin: 0,
      fontSize: tokens.fontSize.base,
      color: tokens.color.gray[500],
      maxWidth: tokens.sizing[64],
      lineHeight: tokens.lineHeight.relaxed,
    };

    const actionStyle: React.CSSProperties = {
      marginTop: tokens.spacing[2],
    };

    return (
      <div ref={ref} className={cx(className)} style={containerStyle} {...props}>
        {icon && <div style={iconStyle} aria-hidden="true">{icon}</div>}
        <h3 style={titleStyle}>{title}</h3>
        {description && <p style={descriptionStyle}>{description}</p>}
        {action && <div style={actionStyle}>{action}</div>}
      </div>
    );
  }
);
EmptyState.displayName = 'EmptyState';
