import type { ChatGPTUser } from '@/app/chatgpt-auth';

export type ProductRole = 'Admin' | 'Analyst' | 'Preview';

export function resolveRole(user: ChatGPTUser | null): ProductRole {
  if (!user) return 'Preview';
  const adminEmails = (process.env.PLATELENS_ADMIN_EMAILS ?? '')
    .split(',')
    .map((email) => email.trim().toLowerCase())
    .filter(Boolean);
  return adminEmails.includes(user.email.toLowerCase()) ? 'Admin' : 'Analyst';
}
