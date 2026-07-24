'use client';

import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from 'react';

import { Icon, type IconName } from './icons';

export function Button({ children, icon, tone = 'default', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { icon?: IconName; tone?: 'default' | 'primary' | 'danger' | 'quiet' }) {
  return <button className={`button button-${tone}`} {...props}>{icon ? <Icon name={icon} /> : null}<span>{children}</span></button>;
}

export function Field({ label, hint, children, wide = false }: { label: string; hint?: string; children: ReactNode; wide?: boolean }) {
  return <label className={`field${wide ? ' field-wide' : ''}`}><span>{label}</span>{children}{hint ? <small>{hint}</small> : null}</label>;
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input className="input" {...props} />;
}

export function Textarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className="input textarea" {...props} />;
}

export function StatusBadge({ status }: { status: string }) {
  return <span className={`status status-${status.toLowerCase()}`}><i />{status}</span>;
}

export function EmptyState({ icon, title, copy, action }: { icon: IconName; title: string; copy: string; action?: ReactNode }) {
  return <div className="empty-state"><span><Icon name={icon} /></span><h3>{title}</h3><p>{copy}</p>{action}</div>;
}

export function Spinner({ label = 'Loading' }: { label?: string }) {
  return <div className="spinner-wrap"><i className="spinner" /><span>{label}</span></div>;
}

export function formatDate(value: string) {
  return new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
}
