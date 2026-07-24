export type LocalizedText = { en: string; ar: string };

export type AdminSession = {
  id: string;
  email: string;
  role: 'ADMIN';
  createdAt: string;
};

export type AdminCategory = {
  id: string;
  slug: string;
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';
  position: number;
  publishedRevision: number | null;
  createdAt: string;
  updatedAt: string;
};

export type CategoryRevision = {
  id: string;
  revision: number;
  label: LocalizedText;
  iconCode: string;
  createdBy: string | null;
  createdAt: string;
};

export type AdminTutorial = {
  id: string;
  slug: string;
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';
  position: number;
  featuredPosition: number | null;
  publishedRevision: number | null;
  createdAt: string;
  updatedAt: string;
};

export type MediaVariants = {
  enLight: string | null;
  enDark: string | null;
  arLight: string | null;
  arDark: string | null;
};

export type MediaSlot = {
  defaultMediaId: string;
  alt: LocalizedText;
  variants: MediaVariants;
};

export type TutorialStep = {
  id: string;
  title: LocalizedText;
  body: LocalizedText;
  tip: LocalizedText | null;
  media: MediaSlot | null;
};

export type TutorialRevision = {
  id: string;
  revision: number;
  categoryId: string;
  title: LocalizedText;
  summary: LocalizedText;
  introduction: LocalizedText;
  duration: LocalizedText;
  level: LocalizedText;
  cover: MediaSlot;
  steps: TutorialStep[];
  createdBy: string | null;
  createdAt: string;
};

export type TutorialMedia = {
  id: string;
  contentType: 'image/jpeg' | 'image/png';
  byteSize: number;
  width: number;
  height: number;
  sha256: string;
  published: boolean;
  createdAt: string;
};

export type NavView = 'overview' | 'tutorials' | 'categories' | 'media';
