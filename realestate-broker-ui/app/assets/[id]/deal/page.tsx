import DealWorkspacePageClient from './DealWorkspacePageClient'

type DealWorkspacePageProps = {
  params: Promise<{ id: string }>
}

export default async function DealWorkspacePage({ params }: DealWorkspacePageProps) {
  const { id } = await params

  return <DealWorkspacePageClient assetId={id} />
}
