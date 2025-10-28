import DealWorkspacePageClient from './DealWorkspacePageClient'

type DealWorkspacePageProps = {
  params: Promise<{ assetId: string }>
}

export default async function DealWorkspacePage({ params }: DealWorkspacePageProps) {
  const { assetId } = await params

  return <DealWorkspacePageClient assetId={assetId} />
}
