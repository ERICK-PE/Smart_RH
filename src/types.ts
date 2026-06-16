export type UserProfile = 'rh_admin' | 'lideranca' | 'funcionario' | 'candidato' | null;

export type SessionUser = {
  id: number;
  username: string;
  nome?: string;
  is_staff: boolean;
  is_superuser: boolean;
  groups: string[];
  permissions: string[];
  profile: UserProfile;
  funcionario_id: number | null;
  candidato_cpf: string | null;
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
  type?: 'text' | 'textarea' | 'number' | 'date' | 'password' | 'email' | 'select';
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

export type ResourceConfig = {
  title: string;
  description: string;
  endpoint: string;
  idField: string;
  columns: Array<{ key: string; label: string }>;
  fields: FieldConfig[];
  searchPlaceholder?: string;
  allowCreate?: boolean;
  allowEdit?: boolean;
  allowDelete?: boolean;
  rowLinks?: Array<{ label: string; to: (record: ApiRecord) => string }>;
};
