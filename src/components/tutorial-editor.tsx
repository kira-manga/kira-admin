'use client';

import { FormEvent, useRef, useState } from 'react';

import type { AdminCategory, LocalizedText, MediaSlot, TutorialMedia, TutorialRevision, TutorialStep } from '@/lib/types';
import { Icon } from './icons';
import { MediaSlotEditor } from './media-slot-editor';
import { Button, Field, Input, Textarea } from './ui';

type RevisionDraft = Omit<TutorialRevision, 'id' | 'revision' | 'createdBy' | 'createdAt'>;
type EditorSection = 'essentials' | 'summary' | 'cover' | 'steps';

const editorSections: Array<{ id: EditorSection; number: string; label: string }> = [
  { id: 'essentials', number: '01', label: 'Essentials' },
  { id: 'summary', number: '02', label: 'Summary' },
  { id: 'cover', number: '03', label: 'Cover media' },
  { id: 'steps', number: '04', label: 'Guide steps' },
];

const blankText = (): LocalizedText => ({ en: '', ar: '' });
const blankSlot = (media: TutorialMedia[]): MediaSlot => ({ defaultMediaId: media[0]?.id ?? '', alt: blankText(), variants: { enLight: null, enDark: null, arLight: null, arDark: null } });
const blankStep = (index: number): TutorialStep => ({ id: `step-${index + 1}`, title: blankText(), body: blankText(), tip: null, media: null });

function initialDraft(base: TutorialRevision | undefined, categories: AdminCategory[], media: TutorialMedia[]): RevisionDraft {
  if (base) return { categoryId: base.categoryId, title: { ...base.title }, summary: { ...base.summary }, introduction: { ...base.introduction }, duration: { ...base.duration }, level: { ...base.level }, cover: structuredClone(base.cover), steps: structuredClone(base.steps) };
  return { categoryId: categories.find((item) => item.status === 'PUBLISHED')?.id ?? categories[0]?.id ?? '', title: blankText(), summary: blankText(), introduction: blankText(), duration: { en: '3 min', ar: '٣ دقائق' }, level: { en: 'Beginner', ar: 'مبتدئ' }, cover: blankSlot(media), steps: [blankStep(0)] };
}

export function TutorialEditor({ slug, base, categories, media, busy, onClose, onSave }: { slug: string; base?: TutorialRevision; categories: AdminCategory[]; media: TutorialMedia[]; busy: boolean; onClose: () => void; onSave: (draft: RevisionDraft, publish: boolean) => Promise<void> }) {
  const [draft, setDraft] = useState(() => initialDraft(base, categories, media));
  const [activeSection, setActiveSection] = useState<EditorSection>('essentials');
  const editorContentRef = useRef<HTMLElement>(null);
  const selectedCategory = categories.find((item) => item.id === draft.categoryId);

  function text(field: keyof Pick<RevisionDraft, 'title' | 'summary' | 'introduction' | 'duration' | 'level'>, language: keyof LocalizedText, value: string) {
    setDraft((current) => ({ ...current, [field]: { ...current[field], [language]: value } }));
  }
  function stepText(index: number, field: 'title' | 'body', language: keyof LocalizedText, value: string) {
    setDraft((current) => ({ ...current, steps: current.steps.map((step, itemIndex) => itemIndex === index ? { ...step, [field]: { ...step[field], [language]: value } } : step) }));
  }
  function tipText(index: number, language: keyof LocalizedText, value: string) {
    setDraft((current) => ({ ...current, steps: current.steps.map((step, itemIndex) => itemIndex === index ? { ...step, tip: { en: step.tip?.en ?? '', ar: step.tip?.ar ?? '', [language]: value } } : step) }));
  }
  function updateStep(index: number, patch: Partial<TutorialStep>) {
    setDraft((current) => ({ ...current, steps: current.steps.map((step, itemIndex) => itemIndex === index ? { ...step, ...patch } : step) }));
  }
  function moveStep(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= draft.steps.length) return;
    const steps = [...draft.steps]; [steps[index], steps[target]] = [steps[target], steps[index]]; setDraft({ ...draft, steps });
  }
  function scrollToSection(section: EditorSection) {
    const container = editorContentRef.current;
    const target = container?.querySelector<HTMLElement>(`#${section}`);
    if (!container || !target) return;

    setActiveSection(section);
    const top = target.getBoundingClientRect().top - container.getBoundingClientRect().top + container.scrollTop;
    container.scrollTo({ top, behavior: 'smooth' });
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    const submitter = (event.nativeEvent as SubmitEvent).submitter as HTMLButtonElement | null;
    const publish = submitter?.value === 'publish';
    const normalized = { ...draft, steps: draft.steps.map((step) => ({ ...step, tip: step.tip?.en.trim() || step.tip?.ar.trim() ? step.tip : null })) };
    await onSave(normalized, publish);
  }

  return (
    <div className="editor-layer">
      <form className="editor" onSubmit={submit}>
        <header className="editor-header"><div><span>NEW REVISION {base ? `· BASED ON V${base.revision}` : ''}</span><h2>{slug}</h2></div><div><Button type="button" onClick={onClose}>Cancel</Button><Button type="submit" name="intent" value="draft" icon="check" disabled={busy}>{busy ? 'Saving…' : 'Save draft'}</Button><Button type="submit" name="intent" value="publish" tone="primary" icon="spark" disabled={busy}>{busy ? 'Publishing…' : 'Save & publish'}</Button><button className="editor-close" type="button" onClick={onClose} aria-label="Close editor"><Icon name="close" /></button></div></header>
        <div className="editor-body">
          <aside className="editor-nav"><p>REVISION SECTIONS</p>{editorSections.map((section) => <button key={section.id} type="button" className={activeSection === section.id ? 'active' : ''} aria-controls={section.id} aria-current={activeSection === section.id ? 'step' : undefined} onClick={() => scrollToSection(section.id)}>{section.number} <span>{section.label}</span></button>)}<div><Icon name="history" /><p>Saving creates an immutable revision. Nothing changes publicly until you publish.</p></div></aside>
          <main className="editor-content" ref={editorContentRef}>
            <section className="editor-section" id="essentials"><div className="section-number">01</div><div className="section-copy"><span>ESSENTIALS</span><h3>Name and classify the guide</h3><p>The slug stays fixed, while every field below becomes part of this new revision.</p></div><div className="form-grid"><Field label="Category" wide hint={selectedCategory ? `Selected: ${selectedCategory.slug}. Save the revision to apply this category change.` : 'Choose the category where this tutorial should appear.'}><select className="input" value={draft.categoryId} onChange={(event) => setDraft((current) => ({ ...current, categoryId: event.target.value }))} required><option value="">Choose a category…</option>{categories.map((item) => <option key={item.id} value={item.id}>{item.slug} · {item.status}</option>)}</select></Field><Field label="English title"><Input value={draft.title.en} onChange={(event) => text('title', 'en', event.target.value)} required /></Field><Field label="Arabic title"><Input dir="rtl" value={draft.title.ar} onChange={(event) => text('title', 'ar', event.target.value)} required /></Field><Field label="English duration"><Input value={draft.duration.en} onChange={(event) => text('duration', 'en', event.target.value)} required /></Field><Field label="Arabic duration"><Input dir="rtl" value={draft.duration.ar} onChange={(event) => text('duration', 'ar', event.target.value)} required /></Field><Field label="English level"><Input value={draft.level.en} onChange={(event) => text('level', 'en', event.target.value)} required /></Field><Field label="Arabic level"><Input dir="rtl" value={draft.level.ar} onChange={(event) => text('level', 'ar', event.target.value)} required /></Field></div></section>

            <section className="editor-section" id="summary"><div className="section-number">02</div><div className="section-copy"><span>SUMMARY</span><h3>Set expectations clearly</h3><p>Use the short summary on cards and the introduction at the start of the guide.</p></div><div className="form-grid"><Field label="English card summary"><Textarea value={draft.summary.en} onChange={(event) => text('summary', 'en', event.target.value)} required /></Field><Field label="Arabic card summary"><Textarea dir="rtl" value={draft.summary.ar} onChange={(event) => text('summary', 'ar', event.target.value)} required /></Field><Field label="English introduction"><Textarea className="input textarea tall" value={draft.introduction.en} onChange={(event) => text('introduction', 'en', event.target.value)} required /></Field><Field label="Arabic introduction"><Textarea className="input textarea tall" dir="rtl" value={draft.introduction.ar} onChange={(event) => text('introduction', 'ar', event.target.value)} required /></Field></div></section>

            <section className="editor-section" id="cover"><div className="section-number">03</div><div className="section-copy"><span>COVER MEDIA</span><h3>Choose the visual identity</h3><p>The default is required. Theme and language variants switch automatically on the public site.</p></div>{media.length ? <MediaSlotEditor value={draft.cover} media={media} onChange={(cover) => setDraft({ ...draft, cover })} /> : <div className="notice notice-error">Upload at least one screenshot before creating a tutorial revision.</div>}</section>

            <section className="editor-section" id="steps"><div className="section-number">04</div><div className="section-copy section-copy-row"><div><span>GUIDE STEPS</span><h3>Build the walkthrough</h3><p>Each guide needs at least one step and supports up to 24.</p></div><Button type="button" icon="plus" disabled={draft.steps.length >= 24} onClick={() => setDraft({ ...draft, steps: [...draft.steps, blankStep(draft.steps.length)] })}>Add step</Button></div><div className="step-editor-list">{draft.steps.map((step, index) => (
              <article className="step-editor" key={`${step.id}-${index}`}>
                <header><span>{String(index + 1).padStart(2, '0')}</span><div><strong>{step.title.en || `Step ${index + 1}`}</strong><small>{step.id}</small></div><div><button type="button" onClick={() => moveStep(index, -1)} disabled={index === 0}><Icon name="chevronUp" /></button><button type="button" onClick={() => moveStep(index, 1)} disabled={index === draft.steps.length - 1}><Icon name="chevronDown" /></button><button type="button" className="danger-icon" onClick={() => setDraft({ ...draft, steps: draft.steps.filter((_, itemIndex) => itemIndex !== index) })} disabled={draft.steps.length === 1}><Icon name="trash" /></button></div></header>
                <div className="form-grid"><Field label="Stable step id" wide hint="Used for page anchors; keep it short and URL-friendly."><Input value={step.id} pattern="[a-zA-Z0-9_-]+" onChange={(event) => updateStep(index, { id: event.target.value })} required /></Field><Field label="English title"><Input value={step.title.en} onChange={(event) => stepText(index, 'title', 'en', event.target.value)} required /></Field><Field label="Arabic title"><Input dir="rtl" value={step.title.ar} onChange={(event) => stepText(index, 'title', 'ar', event.target.value)} required /></Field><Field label="English instructions"><Textarea className="input textarea tall" value={step.body.en} onChange={(event) => stepText(index, 'body', 'en', event.target.value)} required /></Field><Field label="Arabic instructions"><Textarea className="input textarea tall" dir="rtl" value={step.body.ar} onChange={(event) => stepText(index, 'body', 'ar', event.target.value)} required /></Field><Field label="English tip (optional)"><Textarea value={step.tip?.en ?? ''} onChange={(event) => tipText(index, 'en', event.target.value)} /></Field><Field label="Arabic tip (optional)"><Textarea dir="rtl" value={step.tip?.ar ?? ''} onChange={(event) => tipText(index, 'ar', event.target.value)} /></Field></div>
                <div className="step-media-toggle"><label><input type="checkbox" checked={Boolean(step.media)} onChange={(event) => updateStep(index, { media: event.target.checked ? blankSlot(media) : null })} /><span>Add a screenshot to this step</span></label></div>
                {step.media ? <MediaSlotEditor compact value={step.media} media={media} onChange={(slot) => updateStep(index, { media: slot })} /> : null}
              </article>
            ))}</div></section>
          </main>
        </div>
      </form>
    </div>
  );
}
