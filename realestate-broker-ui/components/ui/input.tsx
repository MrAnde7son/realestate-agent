import React from 'react'

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>){
  return <input {...props} className={"rounded-lg bg-[var(--muted)] border border-[var(--border)] px-3 py-2 text-sm outline-none "+(props.className??"")} />
}
