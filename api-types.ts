// 合同审计系统 API 类型定义
// 自动生成，请勿手动修改

export interface ChatRequest {
  session_id: string;
  message: string;
}

export interface ChatResponse {
  session_id: string;
  response: string;
  context_used?: string | null;
  timestamp: string;
  error?: null;
}

export interface CreateSessionRequest {
  user_id: string;
  contract_file?: string | null;
}

export interface HTTPValidationError {
  detail?: any[];
}

export interface LoadContractRequest {
  session_id: string;
  contract_file: string;
}

export interface SessionInfo {
  session_id: string;
  user_id: string;
  contract_file?: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ValidationError {
  loc: any[];
  msg: string;
  type: string;
}

