'use client'

import { useCallback } from 'react'
import { FieldErrors, UseFormReturn } from 'react-hook-form'

/**
 * Standardized form validation hook
 * Provides consistent error handling and validation patterns
 */
export function useFormValidation<T extends Record<string, any>>(
  form: UseFormReturn<T>
) {
  const { formState: { errors }, setError, clearErrors, trigger } = form

  /**
   * Get error message for a field
   */
  const getFieldError = useCallback((fieldName: keyof T): string | undefined => {
    const error = errors[fieldName]
    if (!error) return undefined
    return error.message as string
  }, [errors])

  /**
   * Set field error with consistent messaging
   */
  const setFieldError = useCallback((
    fieldName: keyof T,
    message: string,
    type: 'required' | 'pattern' | 'validate' | 'custom' = 'validate'
  ) => {
    setError(fieldName as any, {
      type,
      message,
    })
  }, [setError])

  /**
   * Clear field error
   */
  const clearFieldError = useCallback((fieldName: keyof T) => {
    clearErrors(fieldName as any)
  }, [clearErrors])

  /**
   * Validate a single field
   */
  const validateField = useCallback(async (fieldName: keyof T): Promise<boolean> => {
    const isValid = await trigger(fieldName as any)
    return isValid
  }, [trigger])

  /**
   * Validate all fields
   */
  const validateAll = useCallback(async (): Promise<boolean> => {
    const isValid = await trigger()
    return isValid
  }, [trigger])

  /**
   * Check if form has any errors
   */
  const hasErrors = Object.keys(errors).length > 0

  /**
   * Get all error messages
   */
  const getAllErrors = useCallback((): Record<string, string> => {
    const errorMessages: Record<string, string> = {}
    Object.keys(errors).forEach((key) => {
      const error = errors[key as keyof T]
      if (error?.message) {
        errorMessages[key] = error.message as string
      }
    })
    return errorMessages
  }, [errors])

  return {
    getFieldError,
    setFieldError,
    clearFieldError,
    validateField,
    validateAll,
    hasErrors,
    getAllErrors,
    errors,
  }
}

