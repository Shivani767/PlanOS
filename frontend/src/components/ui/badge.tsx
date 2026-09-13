import { type HTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

type BadgeVariant = string

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
}

const variantStyles: Record<string, string> = {
  default: 'border-gray-300 bg-gray-100 text-gray-800',
  secondary: 'border-gray-200 bg-gray-50 text-gray-700',
  success: 'border-green-300 bg-green-100 text-green-800',
  warning: 'border-yellow-300 bg-yellow-100 text-yellow-800',
  error: 'border-red-300 bg-red-100 text-red-800',
  info: 'border-blue-300 bg-blue-100 text-blue-800',
  outline: 'border-gray-400 bg-transparent text-gray-700',
  draft: 'border-gray-300 bg-gray-100 text-gray-800',
  active: 'border-green-300 bg-green-100 text-green-800',
  queued: 'border-yellow-300 bg-yellow-100 text-yellow-800',
  running: 'border-blue-300 bg-blue-100 text-blue-800',
  completed: 'border-green-300 bg-green-100 text-green-800',
  failed: 'border-red-300 bg-red-100 text-red-800',
  cancelled: 'border-gray-300 bg-gray-100 text-gray-600',
  pending: 'border-yellow-300 bg-yellow-100 text-yellow-800',
  approved: 'border-green-300 bg-green-100 text-green-800',
  rejected: 'border-red-300 bg-red-100 text-red-800',
}

export function Badge({ className, variant = 'default', children, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors',
        variantStyles[variant] || variantStyles.default,
        className
      )}
      {...props}
    >
      {children}
    </span>
  )
}
