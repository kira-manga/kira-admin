'use client';

import Image from 'next/image';

import { adminMediaUrl } from '@/lib/client-api';
import type { MediaSlot, TutorialMedia } from '@/lib/types';
import { Field, Input } from './ui';

const variantLabels = [
  ['enLight', 'English · Light'],
  ['enDark', 'English · Dark'],
  ['arLight', 'Arabic · Light'],
  ['arDark', 'Arabic · Dark'],
] as const;

export function MediaSlotEditor({ value, media, onChange, compact = false }: { value: MediaSlot; media: TutorialMedia[]; onChange: (value: MediaSlot) => void; compact?: boolean }) {
  const selected = media.find((item) => item.id === value.defaultMediaId);
  function update(patch: Partial<MediaSlot>) { onChange({ ...value, ...patch }); }

  return (
    <div className={`media-slot-editor${compact ? ' compact' : ''}`}>
      <div className="slot-default">
        <div className="slot-preview">{selected ? <Image src={adminMediaUrl(selected.id)} alt="Selected screenshot" width={selected.width} height={selected.height} unoptimized /> : <span>No media selected</span>}</div>
        <Field label="Default screenshot" hint="Used whenever a language/theme-specific image is empty.">
          <select className="input" value={value.defaultMediaId} required onChange={(event) => update({ defaultMediaId: event.target.value })}>
            <option value="">Choose media…</option>
            {media.map((item) => <option key={item.id} value={item.id}>{item.id.slice(0, 8)} · {item.width}×{item.height} · {item.published ? 'in use' : 'available'}</option>)}
          </select>
        </Field>
      </div>
      <div className="form-grid slot-alt"><Field label="English alt text"><Input value={value.alt.en} onChange={(event) => update({ alt: { ...value.alt, en: event.target.value } })} placeholder="Kira Discover screen" required /></Field><Field label="Arabic alt text"><Input value={value.alt.ar} onChange={(event) => update({ alt: { ...value.alt, ar: event.target.value } })} placeholder="شاشة اكتشف في كيرا" dir="rtl" required /></Field></div>
      <div className="variant-grid">{variantLabels.map(([key, label]) => <Field key={key} label={label}><select className="input" value={value.variants[key] ?? ''} onChange={(event) => update({ variants: { ...value.variants, [key]: event.target.value || null } })}><option value="">Use default</option>{media.map((item) => <option key={item.id} value={item.id}>{item.id.slice(0, 8)} · {item.width}×{item.height}</option>)}</select></Field>)}</div>
    </div>
  );
}
