export type UserProfile = 'rh_admin' | 'lideranca' | 'funcionario' | 'candidato' | null;
export type LoginProfile = 'candidato' | 'funcionario' | 'rh';

export type SessionUser = {
  id: number;
  username: string;
  email: string;
  nome?: string;
  is_staff: boolean;
  is_superuser: boolean;
  groups: string[];
  permissions: string[];
  profile: UserProfile;
  funcionario_id: number | null;
  candidato_cpf: string | null;
  is_rh_admin: boolean;
  is_funcionario: boolean;
  is_lideranca: boolean;
  is_candidato: boolean;
};

export type TokenPair = {
  access: string;
  refresh: string;
};

export type PaginatedResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type ApiRecord = Record<string, unknown>;

export type FieldConfig = {
  name: string;
  label: string;
  type?: 'text' | 'textarea' | 'number' | 'date' | 'password' | 'email' | 'select' | 'file';
  required?: boolean;
  readOnly?: boolean;
  options?: Array<{ label: string; value: string }>;
  relation?: {
    endpoint: string;
    idField: string;
    labelField: string;
    secondaryFields?: string[];
  };
};

export type ResourceFilterConfig = {
  name: string;
  label: string;
  type?: 'select' | 'text';
  options?: Array<{ label: string; value: string }>;
};

export type ResourceColumnConfig = {
  key: string;
  label: string;
  maxLength?: number;
};

export type ResourceDetailSectionConfig = {
  title: string;
  fields: Array<{ key: string; label: string }>;
};

export type ResourceConfig = {
  title: string;
  description: string;
  endpoint: string;
  idField: string;
  columns: ResourceColumnConfig[];
  fields: FieldConfig[];
  searchPlaceholder?: string;
  filters?: ResourceFilterConfig[];
  detailSections?: ResourceDetailSectionConfig[];
  allowCreate?: boolean;
  allowEdit?: boolean;
  allowDelete?: boolean;
  rowLinks?: Array<{ label: string; to: (record: ApiRecord) => string }>;
};
