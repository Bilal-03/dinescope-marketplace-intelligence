import Dashboard from '@/app/components/dashboard';
import { getChatGPTUser } from '@/app/chatgpt-auth';
import { resolveRole } from '@/app/lib/access';
import { analytics } from '@/app/lib/analytics';

export const dynamic = 'force-dynamic';

export default async function Home() {
  const user = await getChatGPTUser();
  return <Dashboard data={analytics} displayName={user?.displayName ?? 'Bilal Choudhary'} role={resolveRole(user)} />;
}
