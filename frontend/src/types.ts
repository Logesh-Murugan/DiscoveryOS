export interface Source {
  id: string;
  type: string;
  upload_date: string;
  raw_content: string;
  segment: string;
  use_case?: string;
}

export interface PainPointUnit {
  id: string;
  source_id: string;
  text: string;
  verbatim_quote: string;
  sentiment: 'mild' | 'moderate' | 'severe';
  segment: string;
  use_case: string;
}

export interface Theme {
  id: string;
  label: string;
  pain_point_ids: string[];
  segment_breakdown: Record<string, number>;
  frequency: number;
  severity_score: number;
  segment_value_score: number;
  priority_score: number;
  recommendation: string;
}

export interface ReportObject {
  id: string;
  generated_at: string;
  theme_ids: string[];
  version: number;
}

export interface ReportResponse {
  status: 'success' | 'error';
  report?: ReportObject;
  themes?: Theme[];
  pain_points?: PainPointUnit[];
  markdown?: string;
  message?: string;
  stage?: string;
}
