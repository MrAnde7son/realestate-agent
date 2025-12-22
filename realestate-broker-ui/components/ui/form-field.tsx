'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { AlertCircle } from 'lucide-react'

export interface FormFieldProps {
  label: string
  name: string
  error?: string
  required?: boolean
  description?: string
  className?: string
  children: React.ReactNode
}

export function FormField({
  label,
  name,
  error,
  required,
  description,
  className,
  children,
}: FormFieldProps) {
  const errorId = error ? `${name}-error` : undefined
  const descriptionId = description ? `${name}-description` : undefined

  return (
    <div className={cn('space-y-2', className)}>
      <Label htmlFor={name} className={required ? 'after:content-["*"] after:text-destructive after:ms-1' : ''}>
        {label}
      </Label>
      {description && (
        <p id={descriptionId} className="text-sm text-muted-foreground">
          {description}
        </p>
      )}
      <div className="relative">
        {children}
        {error && (
          <div
            id={errorId}
            role="alert"
            aria-live="polite"
            className="absolute -bottom-5 start-0 flex items-center gap-1 text-sm text-destructive"
          >
            <AlertCircle className="h-3 w-3" aria-hidden="true" />
            <span>{error}</span>
          </div>
        )}
      </div>
      {error && (
        <div className="h-5" aria-hidden="true" />
      )}
    </div>
  )
}

export interface FormInputProps extends React.ComponentPropsWithoutRef<typeof Input> {
  label: string
  error?: string
  required?: boolean
  description?: string
}

export const FormInput = React.forwardRef<HTMLInputElement, FormInputProps>(
  ({ label, name, error, required, description, className, ...props }, ref) => {
    return (
      <FormField
        label={label}
        name={name || ''}
        error={error}
        required={required}
        description={description}
      >
        <Input
          ref={ref}
          id={name}
          name={name}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${name}-error` : description ? `${name}-description` : undefined}
          className={cn(error && 'border-destructive focus-visible:ring-destructive', className)}
          {...props}
        />
      </FormField>
    )
  }
)
FormInput.displayName = 'FormInput'

export interface FormTextareaProps extends React.ComponentPropsWithoutRef<typeof Textarea> {
  label: string
  error?: string
  required?: boolean
  description?: string
}

export const FormTextarea = React.forwardRef<HTMLTextAreaElement, FormTextareaProps>(
  ({ label, name, error, required, description, className, ...props }, ref) => {
    return (
      <FormField
        label={label}
        name={name || ''}
        error={error}
        required={required}
        description={description}
      >
        <Textarea
          ref={ref}
          id={name}
          name={name}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${name}-error` : description ? `${name}-description` : undefined}
          className={cn(error && 'border-destructive focus-visible:ring-destructive', className)}
          {...props}
        />
      </FormField>
    )
  }
)
FormTextarea.displayName = 'FormTextarea'

export interface FormSelectProps extends React.ComponentPropsWithoutRef<typeof SelectTrigger> {
  label: string
  error?: string
  required?: boolean
  description?: string
  placeholder?: string
  children: React.ReactNode
}

export const FormSelect = React.forwardRef<
  React.ElementRef<typeof SelectTrigger>,
  FormSelectProps
>(({ label, name, error, required, description, placeholder, children, className, ...props }, ref) => {
  // Extract Select-specific props and exclude them from SelectTrigger
  const { disabled, onValueChange, value, defaultValue, ...triggerProps } = props as any
  
  return (
    <FormField
      label={label}
      name={name || ''}
      error={error}
      required={required}
      description={description}
    >
      <Select 
        name={name} 
        disabled={disabled}
        onValueChange={onValueChange}
        value={value}
        defaultValue={defaultValue}
      >
        <SelectTrigger
          ref={ref}
          id={name}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${name}-error` : description ? `${name}-description` : undefined}
          className={cn(error && 'border-destructive focus-visible:ring-destructive', className)}
          {...triggerProps}
        >
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          {children}
        </SelectContent>
      </Select>
    </FormField>
  )
})
FormSelect.displayName = 'FormSelect'

