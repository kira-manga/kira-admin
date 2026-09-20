export type LocalizedText = { en: string; ar: string };

export type AdminSession = {
  id: string;
  email: string;
  role: 'ADMIN';
  createdAt: string;
  csrfToken: string;
  generation: string;
  expiresAt: string;
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

export type NavView = 'overview' | 'sources' | 'changesets' | 'audit' | 'tutorials' | 'categories' | 'media' | 'complaints';

export type SourceHead = {
  api: string;
  displayName: string;
  language: string;
  engine: string;
  status: 'draft' | 'withheld' | 'active' | 'disabled' | 'retired' | 'removed';
  siteState?: 'WORKING' | 'UNDER_MAINTENANCE' | 'STOPPED' | 'ADULT_18_PLUS' | null;
  operationalMode?: SourceOperationalMode | null;
  position: number;
  baseUrl: string;
  adult: boolean;
  currentPublishedRevisionNumber: number | null;
  latestRevisionNumber: number | null;
  createdAt: string;
  updatedAt: string;
  publishedAt: string | null;
};

export type SourceOperationalMode = 'enabled' | 'disabled' | 'under_maintenance';

export type SourceOperationalModeResult = {
  api: string;
  mode: SourceOperationalMode;
  sourceRevisionNumber: number;
  documentRevision: number;
  checksum: string;
  noOp: boolean;
};

export type SourceRevision = {
  revisionNumber: number;
  status: 'draft' | 'published' | 'superseded';
  checksum: string;
  createdBy: string;
  createdAt: string;
  publishedAt: string | null;
  valid: boolean | null;
};

export type SourceDraft = {
  id: string;
  basedOnRevisionNumber: number;
  content: string;
  version: number;
  createdBy: string;
  updatedBy: string;
  createdAt: string;
  updatedAt: string;
};

export type ValidationFinding = { code: string; path: string; message: string };
export type ValidationResult = { valid: boolean; errors: ValidationFinding[]; warnings: ValidationFinding[] };

export type SourceCapabilities = {
  sourceSchemaVersion: number;
  catalogSchemaVersion: number;
  canonicalization: string;
  authorableEngines: string[];
  serverLifecycleStates: string[];
  transforms: string[];
  dateStrategies: string[];
  imageStrategies: string[];
  paginationStrategies: string[];
  endpointMethods: string[];
  endpointFormats: string[];
  editorDraftMaxBytes: number;
  optimisticLocking: string;
  publicEnginePolicy: string;
};

export type SourceChange = {
  type: 'publish' | 'disable' | 'enable' | 'retire' | 'remove' | 'reorder';
  api?: string;
  revisionNumber?: number;
  confirm?: string;
  orderedApis?: string[];
};

export type SourceChangeset = {
  id: string;
  name: string;
  description: string | null;
  operations: SourceChange[];
  status: 'open' | 'applied' | 'discarded';
  version: number;
  appliedDocumentRevision: number | null;
  createdBy: string;
  updatedBy: string;
  createdAt: string;
  updatedAt: string;
  appliedAt: string | null;
};

export type AuditEntry = {
  id: number;
  actorUserId: string | null;
  action: string;
  entityType: string;
  entityId: string;
  detail: Record<string, string | number | boolean | null>;
  createdAt: string;
};
