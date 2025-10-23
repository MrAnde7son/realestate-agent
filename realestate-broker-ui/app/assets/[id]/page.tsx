import AssetDetailPageClient from './AssetDetailPageClient'

type AssetDetailPageProps = {
  params: Promise<{ id: string }>
}

export default async function AssetDetailPage({ params }: AssetDetailPageProps) {
  const { id } = await params

  return <AssetDetailPageClient assetId={id} />
}
